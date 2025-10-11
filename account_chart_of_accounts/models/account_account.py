from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    type = fields.Selection(
        selection_add=[('view', 'View')],
        ondelete={'view': 'set default'}

    )
    internal_group = fields.Selection(
        selection_add=[('view', 'View')],
        ondelete={'view': lambda recs: recs.write({'internal_group': 'off_balance'})}
    )

class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"
    _parent_name = "parent_id"
    _parent_store = True

    parent_id = fields.Many2one(
        comodel_name='account.account.template',
        domain=[('internal_type', '=', 'view')]
    )
    parent_path = fields.Char(
        index=True
    )


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def generate_account(self, tax_template_ref, acc_template_ref, code_digits, company):
        temp_model = self.env['account.account.template']
        acc_model = self.env['account.account']
        res = super(AccountChartTemplate, self).generate_account(tax_template_ref, acc_template_ref, code_digits, company)
        for temp, acc in res.items():
            parent = temp_model.browse(temp).parent_id.id
            if parent:
                acc_model.browse(acc).write({'parent_id':res[parent]})
        return res


class AccountAccount(models.Model):
    _inherit = "account.account"
    _parent_name = "parent_id"
    _parent_store = True

    parent_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('internal_type', '=', 'view')]
    )
    parent_path = fields.Char(
        index=True
    )
    child_ids = fields.One2many(
        'account.account', 'parent_id', 'Child Accounts'
    )
    auto_code = fields.Char(
        compute='_get_code', default='0',
        store=True, size=64, index=True
    )
    level = fields.Integer(
        compute="_get_level", store=True, string='Level'
    )
    automticAccountsCodes = fields.Boolean(
        related='company_id.automticAccountsCodes',
    )

    def replace_type_with_internal_type(self,domain):
        # Iterate over each condition and replace if necessary
        new_domain = []
        for condition in domain:
            if isinstance(condition, (list, tuple)) and condition[0] == 'type' and condition[1] == '!=' and condition[
                2] == 'view':
                # Replace ['type', '!=', 'view'] with ['internal_type', '!=', 'view']
                new_domain.append(('internal_type', '!=', 'view'))
            else:
                # Keep the condition as is
                new_domain.append(condition)
        return new_domain

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None: args = []
        domain = args
        domain = self.replace_type_with_internal_type(domain)
        if not self.env.context.get('show_view'):
            domain += [('internal_type', '!=', 'view')]
        return super(AccountAccount, self)._name_search(name, domain, operator ,limit ,name_get_uid)
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        domain = args
        domain = self.replace_type_with_internal_type(domain)
        # if not self.env.context.get('show_view'):
        #     args += [('internal_type', '!=', 'view')]
        return super(AccountAccount, self)._search(domain, offset, limit, order, count, access_rights_uid)
    @api.depends('parent_id')
    def _get_level(self):
        """
        Make the level of the record based on it's parent if not give it
        a zero level cuse it is the first parent account.
        """
        for rec in self:
            level = 0
            if rec.parent_id:
                level = rec.parent_id.level + 1
            if rec.company_id.useFiexedTree and rec.company_id.chart_account_length:
                if level > rec.company_id.chart_account_length:
                    raise UserError(
                        _('''This account level is greater than the chart of account length.'''))
            rec.level = level

    @api.depends('parent_id', 'code', 'parent_id.code')
    def _get_code(self):
        """
        make the code of the record based on it's parent if not give it
        a zero code cuse it is the first parent account.

        :return:
        """
        for rec in self:
            if not rec.company_id.automticAccountsCodes and rec.code:
                rec.auto_code = rec.code
                continue

            code = str(0)
            rec_id = rec.id
            try:
                rec_id = self._origin.id
            except:
                pass
            if rec.parent_id:
                default_padding = self.env.user.company_id.chart_account_padding

                # if the account in the first level padding is not used
                if rec.internal_type == 'view':
                    default_padding = False

                # not to check childs to don't make any serial problems
                parent_code = rec.parent_id.read(['code'])
                parent_code = parent_code[0]['code']
                # if the parent_code is zero make it a null string
                # to don't interupt computation
                parent_code = int(parent_code) != 0 and str(parent_code) or ''
                max_siblings_code = False

                siblings = self.search([
                        ('parent_id', '=', rec.parent_id.id),
                        type(rec_id) == int and ('id', '!=', rec_id) or (1, '=', 1)
                ])

                siblings = [x.read(['code'])[0]['code']
                            for x in siblings]
                if siblings:
                    max_siblings_code = max([int(x) for x in siblings])

                if not max_siblings_code:
                    code = parent_code + \
                                  str(1).zfill(default_padding)
                if max_siblings_code:
                    code = str(max_siblings_code + 1)
            rec.write({'code': code, 'auto_code': code})
            #if rec.child_ids:
            #    rec.child_ids._get_code(code)
