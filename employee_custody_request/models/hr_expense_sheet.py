from odoo import api, fields, models, tools, _
import ast
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrExpenseSheetPledge(models.Model):
    _inherit = "hr.expense.sheet"

    available_account_payment_method_ids = fields.Many2many('account.payment.method.line',
                                                            compute="_compute_available_account_payment_method_ids")
    account_payment_method_id = fields.Many2one('account.payment.method.line', default=False)
    payment_account_id = fields.Many2one(
        comodel_name='account.account',
        check_company=True,
        copy=False,
        ondelete='restrict', )

    custody_bank_journal_id = fields.Many2one(
        'account.journal',
        string='Custody Journal',
        domain=[('custody_journal', '=', True)],
    )
    custody_partner_id = fields.Many2one('res.partner', string='Custody Partner')

    @api.depends('custody_bank_journal_id', 'bank_journal_id')
    def _compute_available_account_payment_method_ids(self):
        AccountPaymentMethodLine = self.env['account.payment.method.line'].sudo()
        for rec in self:
            if rec.payment_mode == 'custody' and rec.custody_bank_journal_id:
                rec.available_account_payment_method_ids = AccountPaymentMethodLine.search(
                    [('id', 'in', rec.custody_bank_journal_id.outbound_payment_method_line_ids.ids)])
            elif rec.bank_journal_id:
                rec.available_account_payment_method_ids = AccountPaymentMethodLine.search(
                    [('id', 'in', rec.bank_journal_id.outbound_payment_method_line_ids.ids)])
            else:
                rec.available_account_payment_method_ids = False

    def action_submit_sheet(self):
        for rec in self:
            if rec.payment_mode == 'custody' and not rec.custody_partner_id:
                raise UserError(
                    _("When the payment type is custody, you must set the Custody Partner before submitting."))
        return super(HrExpenseSheetPledge, self).action_submit_sheet()

    def _get_custody_partner_domain(self):
        if not self.custody_bank_journal_id:
            return [('id', '=', False)]

        pledge_requests = self.env['hr.request.pledge'].search([
            ('journal_id', '=', self.custody_bank_journal_id.id),
            ('remaining_amount', '>', 0),
        ])
        employee_ids = pledge_requests.mapped('employee_id')
        partner_ids = []
        for employee in employee_ids:
            if employee.user_id and employee.user_id.partner_id:
                partner_ids.append(employee.user_id.partner_id.id)
        if not partner_ids:
            return [('id', '=', False)]
        return [('id', 'in', partner_ids)]

    @api.onchange('payment_mode')
    def _onchange_payment_mode(self):
        """Reset fields when payment mode changes"""
        if self.payment_mode == 'custody':
            self.bank_journal_id = False
            self.account_payment_method_id = False
            self.custody_partner_id = False
        else:
            self.custody_bank_journal_id = False
            self.custody_partner_id = False

    @api.onchange('custody_bank_journal_id')
    def _onchange_custody_bank_journal_id(self):
        if self.custody_bank_journal_id:
            self.journal_id = self.custody_bank_journal_id
            self.bank_journal_id = self.custody_bank_journal_id

        self.account_payment_method_id = False
        self.custody_partner_id = False
        return {'domain': {'custody_partner_id': self._get_custody_partner_domain()}}

    @api.onchange('bank_journal_id')
    def _onchange_bank_journal_id(self):
        self.account_payment_method_id = False
        if self.payment_mode == 'custody':
            self.custody_partner_id = False
            return {'domain': {'custody_partner_id': self._get_custody_partner_domain()}}

    def action_sheet_move_create(self):
        """Override to handle custody like company_account"""
        res = super().action_sheet_move_create()

        custody_sheets = self.filtered(lambda sheet: sheet.payment_mode == 'custody' and sheet.expense_line_ids)
        if custody_sheets:
            custody_sheets.paid_expense_sheets()

        return res
