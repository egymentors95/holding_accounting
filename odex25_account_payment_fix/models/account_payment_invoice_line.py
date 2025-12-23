from odoo import models, fields, api


class AccountPaymentInvoiceLine(models.Model):
    _name = 'account.payment.invoice.line'
    _description = 'Account Payment Invoice Line'

    name = fields.Char(string='Name')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    amount_total = fields.Monetary(string='Total Amount', compute='_get_amount_total', store=True)
    amount_residual = fields.Monetary(string='Amount Residual', compute='_get_amount_residual', store=True)
    invoice_date = fields.Date(string='Invoice Date', compute='_get_invoice_date', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_get_currency_id', store=True)
    payment = fields.Float(string="Payment", compute='_get_payment', store=True)


    @api.depends('amount_total', 'amount_residual')
    def _get_payment(self):
        for rec in self:
            if rec.amount_total and rec.amount_residual:
                rec.payment = rec.amount_total - rec.amount_residual

    @api.depends('invoice_id', 'invoice_id.amount_total')
    def _get_amount_total(self):
        for rec in self:
            if rec.invoice_id.amount_total:
                rec.amount_total = rec.invoice_id.amount_total

    @api.depends('invoice_id', 'invoice_id.amount_residual')
    def _get_amount_residual(self):
        for rec in self:
            if rec.invoice_id.amount_residual:
                rec.amount_residual = rec.invoice_id.amount_residual


    @api.depends('invoice_id', 'invoice_id.invoice_date')
    def _get_invoice_date(self):
        for rec in self:
            if rec.invoice_id.invoice_date:
                rec.invoice_date = rec.invoice_id.invoice_date


    @api.depends('invoice_id', 'invoice_id.currency_id')
    def _get_currency_id(self):
        for rec in self:
            if rec.invoice_id.currency_id:
                rec.currency_id = rec.invoice_id.currency_id.id