# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    asset_model = fields.Many2one('account.asset',
                                  domain=lambda self: [('state', '=', 'model'), ('asset_type', '=', self.asset_type)],
                                  help="If this is selected, an expense/revenue will be created automatically when Journal Items on this account are posted.")
    create_asset = fields.Selection([('no', 'No'), ('draft', 'Create in draft'), ('validate', 'Create and validate')],
                                    required=True, default='no')
    can_create_asset = fields.Boolean(compute="_compute_can_create_asset",
                                      help="""Technical field specifying if the account can generate asset depending on it's type. It is used in the account form view.""")
    form_view_ref = fields.Char(compute='_compute_can_create_asset')
    asset_type = fields.Selection(
        [('sale', 'Deferred Revenue'), ('expense', 'Deferred Expense'), ('purchase', 'Asset')],
        compute='_compute_can_create_asset')
    # decimal quantities are not supported, quantities are rounded to the lower int
    multiple_assets_per_line = fields.Boolean(string='Multiple Assets per Line', default=False,
                                              help="Multiple asset items will be generated depending on the bill line quantity instead of 1 global asset.")

    @api.depends('user_type_id')
    def _compute_can_create_asset(self):
        for record in self:
            if record.auto_generate_asset():
                record.asset_type = 'purchase'
            elif record.auto_generate_deferred_revenue():
                record.asset_type = 'sale'
            elif record.auto_generate_deferred_expense():
                record.asset_type = 'expense'
            else:
                record.asset_type = False

            record.can_create_asset = record.asset_type != False

            record.form_view_ref = {
                'purchase': 'odex25_account_asset.view_account_asset_form',
                'sale': 'odex25_account_asset.view_account_asset_revenue_form',
                'expense': 'odex25_account_asset.view_account_asset_expense_form',
            }.get(record.asset_type)

    def auto_generate_asset(self):
        return self.user_type_id in self.get_asset_accounts_type()

    def auto_generate_deferred_revenue(self):
        return self.user_type_id in self.get_deferred_revenue_accounts_type()

    def auto_generate_deferred_expense(self):
        return self.user_type_id in self.get_deferred_expense_accounts_type()

    def get_asset_accounts_type(self):
        return self.env.ref('account.data_account_type_fixed_assets') + self.env.ref(
            'account.data_account_type_non_current_assets')

    def get_deferred_revenue_accounts_type(self):
        return self.env.ref('account.data_account_type_current_liabilities') + self.env.ref(
            'account.data_account_type_non_current_liabilities')

    def get_deferred_expense_accounts_type(self):
        return self.env.ref('account.data_account_type_current_assets') + self.env.ref(
            'account.data_account_type_prepayments')

    _sql_constraints = [
        ('code_company_uniq', 'unique (name)', 'The code of the account must be unique per company !')
    ]

    @api.model
    def init(self):
        self._cr.execute("ALTER TABLE account_account DROP CONSTRAINT IF EXISTS code_company_uniq;")

    @api.model
    def create(self, vals):
        if self.env.context.get('skip_child_sync'):
            return super().create(vals)

        account = super().create(vals)

        self._cr.execute("ALTER TABLE account_account DROP CONSTRAINT IF EXISTS code_company_uniq;")

        company = self.env['res.company'].browse(
            self.env.context.get('company_id', self.env).company.id
        )

        if company:
            child_companies = self.env['res.company'].search([('parent_id', '=', company.id)])
            for child_company in child_companies:
                vals_copy = vals.copy()
                vals_copy['company_id'] = child_company.id
                self.with_context(skip_child_sync=True).sudo().create(vals_copy)

        return account

    def write(self, vals):
        # if self.env.context.get('skip_child_sync'):
        #     return super().write(vals)

        res = super().write(vals)
        # company = self.env['res.company'].browse(
        #     self.env.context.get('company_id', self.env).company.id
        # )
        for account in self:
                # company = account.company_id
            # print("company" , account.company_id.name)
            child_companies = self.env['res.company'].search([('parent_id', '=', account.company_id.id)])
            # print("child_companies", child_companies.name)
            for child_company in child_companies:
                child_account = self.env['account.account'].sudo().search([
                    ('code', '=', account.code),
                    ('company_id', '=', child_company.id)
                ], limit=1)
                # print("child_account", child_account)
                if child_account:
                    child_account.with_context(skip_child_sync=True).sudo().write(vals)

        return res
