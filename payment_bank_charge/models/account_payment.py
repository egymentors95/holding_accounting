from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    bank_charge = fields.Boolean("Bank charges")


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _cleanup_write_orm_values(self, record, vals):
        cleaned_vals = super(AccountMove, self)._cleanup_write_orm_values(record, vals)
        # TODO check if record is instant of account.payment
        if cleaned_vals.get('amount', False):
            cleaned_vals['amount'] = cleaned_vals['amount'] + record.bank_charge_amount + record.bank_tax_amount
        return cleaned_vals


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    bank_charge_bool = fields.Boolean("Bank charges", tracking=True)
    charge_type = fields.Selection(selection=[('fixed', 'Fixed'), ('percent', 'Percent')], string='Charge Type',
                                   tracking=True)
    charge_amount = fields.Float(string='Charge Value', tracking=True)
    bank_charge_account_id = fields.Many2one("account.account", "Bank charge account", tracking=True)
    tax_id = fields.Many2one('account.tax', string='Default Taxes', tracking=True)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bank_charge_amount = fields.Monetary("Bank charges amount", compute='_get_charge_value', tracking=True)
    bank_tax_amount = fields.Monetary("Bank Taxes amount", compute='_get_tax_value', tracking=True)
    tax_account_id = fields.Many2one("account.account", "Fees Tax Account")

    @api.constrains('payment_method_id')
    def _check_bank_charge_amount(self):
        for pay in self:
            if pay.bank_charge_amount > pay.amount:
                raise ValidationError(_("Bank charges amount must not be more than Payment amount."))

    @api.depends('payment_method_id', 'payment_method_id.bank_charge_bool')
    def _get_charge_value(self):
        for item in self:
            item.bank_charge_amount = 0
            if item.payment_method_id:
                if item.payment_method_id.bank_charge_bool:
                    if item.payment_method_id.charge_type == 'fixed':
                        item.bank_charge_amount = item.payment_method_id.charge_amount
                    else:
                        if item.amount:
                            item.bank_charge_amount = item.amount - (
                                    item.amount * (1 - (item.payment_method_id.charge_amount or 0.0) / 100.0))
                else:
                    item.bank_charge_amount = 0
            else:
                item.bank_charge_amount = 0

    @api.depends('payment_method_id', 'payment_method_id.tax_id', 'bank_charge_amount')
    def _get_tax_value(self):
        for item in self:
            if item.payment_method_id:
                if item.payment_method_id.tax_id:
                    tax_res = item.payment_method_id.tax_id.compute_all(item.bank_charge_amount)
                    tax_amount = tax_res['taxes'][0]['amount']
                    item.bank_tax_amount = tax_amount
                    item.tax_account_id = tax_res['taxes'][0]['account_id']
                else:
                    item.bank_tax_amount = 0
            else:
                item.bank_tax_amount = 0

    def _seek_for_lines(self):
        ''' inherit to execlude bank fees lines
        '''
        fees_line = self.env['account.move.line']
        liquidity_lines, counterpart_lines, writeoff_lines = super(AccountPayment, self)._seek_for_lines()
        for line in self.move_id.line_ids:
            if line.bank_charge:
                fees_line += line
            liquidity_lines -= fees_line
            counterpart_lines -= fees_line
            writeoff_lines -= fees_line
        return liquidity_lines, counterpart_lines, writeoff_lines

    def _seek_for_fees_lines(self):
        ''' get bank fees lines
        '''
        fees_line = self.env['account.move.line']
        for line in self.move_id.line_ids:
            if line.bank_charge:
                fees_line += line
        return fees_line

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' inherit to add bank fees .
        '''
        tax_amount = 0.0
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals)
        if self.move_id:
            fess_lines = self.move_id.mapped('line_ids').filtered(lambda l: l.bank_charge == True)
            if fess_lines:
                fess_lines.with_context(check_move_validity=False).unlink()
        # Compute amounts.
        if self.payment_type == 'inbound':
            # Receive money.
            counterpart_amount_currency = self.bank_charge_amount - self.bank_tax_amount
        else:
            # Send money.
            counterpart_amount_currency = -self.bank_charge_amount + self.bank_tax_amount
        counterpart_balance = self.currency_id._convert(
            counterpart_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        currency_id = self.currency_id.id
        if self.payment_method_id.payment_type == 'inbound':
            if self.payment_method_id.bank_charge_bool:
                # for line in line_vals_list:
                # if line['account_id'] in (
                #         self.journal_id.default_account_id.id,
                #         self.journal_id.payment_debit_account_id.id,
                #         self.journal_id.payment_credit_account_id.id) and not line.get('bank_charge', False):
                #     line['debit'] = line['debit'] - abs(counterpart_balance)
                #     line['amount_currency'] = line['amount_currency'] - counterpart_amount_currency
                line_vals_list.append({
                    'name': 'Payment Method Fees',
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.payment_method_id.bank_charge_account_id.id,
                    'bank_charge': True,
                })
                line_vals_list.append({
                    'name': 'Bank Payment Method Fees',
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': 0.0,
                    'credit': counterpart_balance,
                    'partner_id': self.partner_id.id,
                    'account_id': self.journal_id.default_account_id.id,
                    'bank_charge': True,

                })
            if self.payment_method_id.tax_id:
                tax_amount = self.bank_tax_amount
                if tax_amount:
                    # for l in line_vals_list:
                    #     if l['account_id'] in (
                    #             self.journal_id.default_account_id.id,
                    #             self.journal_id.payment_debit_account_id.id,
                    #             self.journal_id.payment_credit_account_id.id) and not l.get('bank_charge', False):
                    #         l['debit'] = l['debit'] - abs(tax_amount)
                    #         l['amount_currency'] = l['amount_currency'] - tax_amount
                    line_vals_list.append({
                        'name': 'Payment Method Tax',
                        'date_maturity': self.date,
                        'currency_id': currency_id,
                        'debit': abs(tax_amount),
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.tax_account_id.id,
                        'bank_charge': True,
                    })
                    line_vals_list.append({
                        'name': 'Bank Payment Method Tax',
                        'date_maturity': self.date,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': abs(tax_amount),
                        'partner_id': self.partner_id.id,
                        'account_id': self.journal_id.default_account_id.id,
                        'bank_charge': True,
                    })
        return line_vals_list
