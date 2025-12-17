from odoo import models, fields, api


class AccountPaymentInvoiceLine(models.Model):
    _name = 'account.payment.invoice.line'
    _description = 'Account Payment Invoice Line'

    name = fields.Char(string='Name')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    amount_total = fields.Monetary(string='Total Amount', related='invoice_id.amount_total')
    amount_residual = fields.Monetary(string='Amount Residual', related='invoice_id.amount_residual')
    invoice_date = fields.Date(string='Invoice Date', related='invoice_id.invoice_date')
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice_id.currency_id')


