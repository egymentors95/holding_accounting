# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    cheque = fields.Boolean(related='payment_method_id.cheque')
    agent_id = fields.Many2one('res.partner', 'Agent')
    payment_method_no = fields.Char(string='Cheque / Transfer Ref')
    payment_method_date = fields.Date(string='Date')

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        payment_vals['agent_id'] = self.agent_id.id
        payment_vals['payment_method_no'] = self.payment_method_no
        payment_vals['payment_method_date'] = self.payment_method_date
        return payment_vals