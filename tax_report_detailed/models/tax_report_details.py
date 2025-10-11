from odoo import models, fields


class TaxReportDetails(models.TransientModel):
    _name = 'tax.report.details'
    _description = 'Tax Report Details'


    num = fields.Char(string='Invoice No')
    desc = fields.Char(string='Description')
    date = fields.Date()
    tax_id = fields.Many2one(comodel_name='account.tax', string='Tax Name')
    tax_name = fields.Char()
    record_type = fields.Selection(selection=[('sale', 'Sales'), ('purchase', 'Purchase'),
                                              ('in_refund', 'In Refund'), ('out_refund', 'Out Refund')], string='Type')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    partner_name = fields.Char()
    vat = fields.Char(related='partner_id.vat')
    amount_exclude = fields.Float(string='Amount Without Tax')
    amount_tax = fields.Float(string='Tax amount')
    total_amount = fields.Float(string='Total Amount')

