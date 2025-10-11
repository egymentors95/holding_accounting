# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.osv import expression

from odoo.exceptions import UserError, ValidationError


class PettyCash(models.Model):
    _name = "petty.cash"
    _description = "Petty Cash"
    _rec_name = "display_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    serial = fields.Char(readonly=True)
    name = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}, tracking=True
    )
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Petty Cash Holder", required=True,
        readonly=True, states={"draft": [("readonly", False)]}, default=lambda self: self.env.user.partner_id.id
        , tracking=True)
    account_id = fields.Many2one(comodel_name="account.account", string="Petty Cash Account", tracking=True)
    petty_cash_limit = fields.Float(string="Amount", required=True, readonly=True,
                                    states={"draft": [("readonly", False)]}, tracking=True)
    petty_cash_balance = fields.Float(string="Balance", compute="_compute_petty_cash_balance", readonly=True,
                                      tracking=True)
    petty_cash_expenses = fields.Float(string="Expenses", compute="_compute_petty_cash_expenses", readonly=True,
                                       tracking=True)
    replace_amount = fields.Float(string="Replace Amount", compute="_compute_replace_amount", readonly=True,
                                  tracking=True)
    total_replace_amount = fields.Float(string="Total Petty Amount", compute="_compute_total_replace_amount",
                                        readonly=True, tracking=True)
    petty_cash_remaining = fields.Float(string="Petty Cash Remaining", compute="_compute_petty_cash_remaining", readonly=True,
                                        tracking=True)
    journal_id = fields.Many2one(comodel_name="account.journal", traching=True)
    date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        readonly=True, states={"draft": [("readonly", False)]}, tracking=True,
    )
    type = fields.Selection(selection=[('continuous', 'Continuous'), ('temporary', 'Temporary')], tracking=True)
    percent_to_reconcile = fields.Float('Percent To Reconcile', tracking=True)
    expense_limit = fields.Integer('Expense Limit', tracking=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('submitted', 'Submitted'),
                   ('running', 'Running'), ('closed', 'Reconciled'),
                   ('reject', 'Reject')], tracking=True,
        default='draft', readonly=True, states={"draft": [("readonly", False)]}
    )
    invoice_ids = fields.One2many(
        'account.move', 'petty_cash_id'
    )
    invoice_count = fields.Integer(
        compute='_invoice_count',
        string='# Done of Invoices', tracking=True
    )
    is_invoice_posted = fields.Boolean(string="Invoice Posted", compute='_compute_is_invoice_posted', store=False)

    payment_count = fields.Integer(
        compute='_payment_count',
        string='# of Payments',
        help="Number of Payments"
    )
    is_paid = fields.Boolean(string="Paid", store=True)
    expense_report_count = fields.Integer(
        compute='_expense_report_count',
        string='# of Expenses Reports',
        help="Number of  Expenses Reports"
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company, states={"draft": [("readonly", False)]}
    )
    move_line_ids = fields.One2many(
        'account.move.line', 'petty_cash_id'
    )

    petty_configuration_id = fields.Many2one(comodel_name="petty.cash.configuration", string="Petty", required=False,
                                             states={"draft": [("readonly", False)]})

    @api.depends('name', 'serial')
    def _compute_display_name(self):
        for rec in self:
            if rec.serial:
                rec.display_name = rec.serial + " - " + rec.name
            else:
                rec.display_name = rec.name

    @api.onchange('petty_configuration_id')
    def onchange_petty_configuration_id(self):
        if self.petty_configuration_id:
            self.account_id = self.petty_configuration_id.account_id.id
            self.journal_id = self.petty_configuration_id.journal_id.id
            self.type = self.petty_configuration_id.type
            self.percent_to_reconcile = self.petty_configuration_id.percent_to_reconcile
            self.expense_limit = self.petty_configuration_id.expense_limit

    @api.constrains("petty_configuration_id", "petty_cash_limit")
    def _check_expense_limit(self):
        if self.petty_configuration_id and self.petty_configuration_id.petty_cash_limit < self.petty_cash_limit:
            raise UserError(
                _('Amount can not exceed the limit (%s)') % self.petty_configuration_id.petty_cash_limit)

    @api.constrains("petty_cash_limit")
    def _check_petty_cash_limit(self):
        if self.petty_cash_limit <= 0:
            raise UserError(_('Amount can not be equal or less than zero'))

    @api.depends('invoice_ids')
    def _compute_is_invoice_posted(self):
        for rec in self:
            if any([line.state == 'posted' for line in self.invoice_ids]):
                rec.is_invoice_posted = True
            else:
                rec.is_invoice_posted = False

    def _invoice_count(self):
        self.invoice_count = len(self.invoice_ids.filtered(lambda x: x.move_type == 'in_invoice'))

    def _payment_count(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count([('petty_cash_id', '=', rec.id)])

    def _expense_report_count(self):
        self.expense_report_count = len(self.env['hr.expense.sheet'].search([('petty_cash_id', '=', self.id)]))

    def open_invoice(self):
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('petty_cash_id', '=', self.id), ('move_type', 'in', ['in_invoice'])],
            'context': {'default_move_type': 'in_invoice',
                        'default_is_petty_cash': True,
                        'default_partner_id': self.partner_id.id,
                        'default_journal_id': self.journal_id.id,
                        'default_petty_cash_id': self.id},
            'view_mode': 'tree,form',
            # 'view_id': self.env.ref('account.view_in_invoice_tree').id
        }

    def open_payment(self):
        # payment_move_line_ids = [r[2].id for inv in self.invoice_ids for r in inv._get_reconciled_invoices_partials()]
        return {
            'name': _('Payment'),
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'domain': [('petty_cash_id', '=', self.id)],
            "context": {'group_by': ['payment_type']},
            'flags': {'search_view': True, 'action_buttons': False},
        }

    def open_expense_report(self):
        user_id = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)])
        return {
            'name': _('Expense Report'),
            'view_mode': 'tree,form',
            'res_model': 'hr.expense.sheet',
            'type': 'ir.actions.act_window',
            'domain': [('petty_cash_id', '=', self.id)],
            'context': {
                "default_petty_cash_id": self.id,
                'default_payment_mode': 'petty_cash',
                'default_employee_id': user_id.employee_ids[0].id if user_id.employee_ids else False,
                'default_user_id': user_id.id,
            },
            'flags': {'search_view': True, 'action_buttons': True},
        }

    @api.model
    def create(self, values):
        values['serial'] = self.env['ir.sequence'].with_context(
            ir_sequence_date=values['date']).next_by_code('petty.cash.seq')
        return super().create(values)

    def act_submit(self):
        self.state = 'submitted'

    # def act_confirm(self):
    #     self.state = 'running'
    def act_confirm(self):
        petty= self.env['petty.cash'].search([('state','=','running')])
        if len(petty)!=0:
            for rec in petty:
                print('for.....')
                if self.partner_id.id == rec.partner_id.id and rec.state=='running':
                    print('on')
                    return {
                        'name': _('Cancel Request Reason'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'petty.cash.cancel.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_reason': rec.name+rec.serial,
                        },
                    }

        self.state = 'running'

    def act_check_balance_to_close(self):
        if self.petty_cash_remaining <= 0:
            self.state = 'closed'

    def act_reject(self):
        self.state = 'reject'

    def act_draft(self):
        self.state = 'draft'

    def unlink(self):
        for i in self:
            if i.state != 'draft':
                raise ValidationError(_('You can not delete record in state not in draft'))
        return super().unlink()

    def _compute_replace_amount(self):
        for rec in self:
            rec.replace_amount = sum(self.env['hr.expense.sheet'].search(
                [('petty_cash_id', '=', self.id)]).filtered(
                lambda line: line.petty_cash_type == 'renew' and line.state == 'post').mapped(
                'total_amount'))

    @api.depends('replace_amount', 'petty_cash_limit')
    def _compute_total_replace_amount(self):
        for rec in self:
            rec.total_replace_amount = rec.petty_cash_limit + rec.replace_amount

    def _compute_petty_cash_expenses(self):
        for rec in self:
            rec.petty_cash_expenses = sum(self.env['hr.expense.sheet'].search(
                [('petty_cash_id', '=', rec.id)]).filtered(lambda line: line.petty_cash_type != 'renew').mapped(
                'total_amount'))

    @api.depends("petty_cash_expenses", "petty_cash_limit")
    def _compute_petty_cash_remaining(self):
        for rec in self:
            rec.petty_cash_remaining = rec.petty_cash_limit - rec.petty_cash_expenses

    @api.depends("partner_id", "account_id", "move_line_ids")
    def _compute_petty_cash_balance(self):
        aml_env = self.env["account.move.line"]
        for rec in self:
            aml = aml_env.search(
                [
                    ("partner_id", "=", rec.partner_id.id),
                    ("account_id", "=", rec.account_id.id),
                    ("parent_state", "=", "posted"),
                    ("petty_cash_id", "=", rec.id),
                ]
            )
            balance = sum([line.debit - line.credit for line in aml])
            rec.petty_cash_balance = balance
            if abs(rec.petty_cash_balance) == rec.petty_cash_limit:
                rec.state = 'closed'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', operator, name), ('serial', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    petty_cash_count = fields.Integer(compute='_compute_petty_cash_count')
    def _compute_petty_cash_count(self):
        for emp in self:
            items = self.env['petty.cash'].search([
                ('partner_id', '=', emp.user_id.partner_id.id),
            ])
            emp.petty_cash_count = len(items)
    def get_pettycach(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicles',
            'view_mode': 'tree',
            'res_model': 'petty.cash',
            'domain': [('partner_id', '=', self.user_id.partner_id.id)],
            'context': "{'create': False}"
        }

