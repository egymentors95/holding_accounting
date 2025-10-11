# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2022 (<http://www.exp-sa.com/>).
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentMethod(models.Model):
    _name = 'account.payment.method'
    _inherit = ['mail.thread', 'account.payment.method']

    cheque = fields.Boolean('Cheque', tracking=True)

    @api.constrains('cheque')
    def _check_cheque(self):
        '''
        chech payment method check to be unique
        '''
        if self.cheque:
            payment_method_ids = self.search(
                [('id', '!=', self.id), ('cheque', '=', True), ('payment_type', '=', self.payment_type)])
            if payment_method_ids:
                raise UserError(_("Payment method with type cheque already exist"))


class AccountPayment(models.Model):
    _inherit = "account.payment"

    cheque = fields.Boolean(related='payment_method_id.cheque')
    clear = fields.Boolean(copy=False)
    agent_id = fields.Many2one('res.partner', 'Agent')
    payment_method_no = fields.Char(string='Cheque / Transfer Ref')
    payment_method_date = fields.Date(string='Date')
    # bank_account_id = fields.Many2one(comodel_name='res.partner.bank', string='Bank No.')
    clear_move_id = fields.Many2one(comodel_name='account.move', string='Clearence Journal Entry', readonly=True,
                                    ondelete='cascade', check_company=True, copy=False)

    cheque_collection_type = fields.Selection(string="Cheque Collection Type",
                                              selection=[('wallet', 'Wallet'),
                                                         ('collection_fee', 'Collection Fee'),
                                                         ('collector', 'Collector'),
                                                         ('mjir', 'Mijr'),
                                                         ('return', 'Return'), ], default='wallet', )

    @api.model
    def _get_method_codes_using_bank_account(self):
        vals_list = super(AccountPayment, self)._get_method_codes_using_bank_account()
        vals_list.append('check_printing')
        return vals_list

    @api.model
    def _get_method_codes_needing_bank_account(self):
        vals_list = super(AccountPayment, self)._get_method_codes_needing_bank_account()
        vals_list.append('check_printing')
        return vals_list

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' inherit to us journals outstanding accounts just incase of payment method check .
        '''
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals)
        if not self.payment_method_id.cheque and not self.is_internal_transfer:
            for line in line_vals_list:
                if line['account_id'] in (
                        self.journal_id.payment_credit_account_id.id, self.journal_id.payment_debit_account_id.id):
                    line['account_id'] = self.journal_id.default_account_id.id
        return line_vals_list

    def clear_check(self):
        values = {}
        values['journal_id'] = self.journal_id.id
        values['ref'] = (self.name or '') + ' ' + (self.payment_method_no or '')
        # Compute amounts.
        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = -self.amount
        else:
            # Send money.
            liquidity_amount_currency = self.amount

        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        currency_id = self.currency_id.id
        liquidity_line_name = self.payment_reference
        counterpart_amount_currency = -liquidity_amount_currency
        counterpart_balance = -liquidity_balance

        # Compute a default label to set on the journal items.

        payment_display_name = self._prepare_payment_display_name()

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name[
                '%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )
        account_id = liquidity_balance > 0.0 and self.journal_id.payment_credit_account_id.id or self.journal_id.payment_debit_account_id.id
        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': account_id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.journal_id.default_account_id.id,
            },
        ]
        values['line_ids'] = [(0, 0, line_vals) for line_vals in line_vals_list]
        clear_move_id = self.env['account.move'].create(values)
        if clear_move_id:
            clear_move_id.post()
            self.clear = True
            self.clear_move_id = clear_move_id.id
            (self.move_id.mapped('line_ids').filtered(
                lambda x: x.account_id.id == account_id) + self.clear_move_id.mapped('line_ids').filtered(
                lambda x: x.account_id.id == account_id)).reconcile()
        return True
