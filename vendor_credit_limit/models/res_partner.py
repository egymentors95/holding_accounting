from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    agreement_limit = fields.Boolean('Agreement Limit')
    limit_ids = fields.One2many('vendor.limit.lines', 'vendor_id')




class LimitLines(models.Model):
    _name = 'vendor.limit.lines'
    _description = "Vendor Limit Lines"

    vendor_id = fields.Many2one('res.partner')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    period = fields.Integer("Allowed Period (Days)", help="The number of days for the credit limit period")
    used_period = fields.Integer("Used Period")
    remaining_period = fields.Integer("Remaining Period", compute="_compute_remaining_period", store=True)
    opening_balance = fields.Float("Opening Balance", digits=(8, 2))
    upper_limit = fields.Float("Upper Limit", digits=(8, 2), compute="compute_upper_limit", store=True, readonly=False)
    used_credit = fields.Float("Used Credit", digits=(8, 2), readonly=True)
    residual_credit = fields.Float("Residual Credit", digits=(8, 2), compute="_compute_residual_credit", store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    note = fields.Char()
    attachment = fields.Binary("Attach File")

    @api.depends('upper_limit', 'used_credit','opening_balance')
    def _compute_residual_credit(self):
        for rec in self:
            if rec.upper_limit > 0 and rec.opening_balance:
                rec.residual_credit = rec.upper_limit - rec.used_credit - rec.opening_balance

    @api.depends('opening_balance')
    def compute_upper_limit(self):
        for rec in self:
            if rec.opening_balance > 0:
                rec.upper_limit -= rec.opening_balance
            else:
                rec.upper_limit = 0.0

    @api.depends('period', 'used_period')
    def _compute_remaining_period(self):
        for rec in self:
            if rec.period > 0:
                rec.remaining_period = rec.period - rec.used_period
            else:
                rec.remaining_period = 0

    @api.model
    def calculate_remaining_period(self):
        records = self.search([('period', '>', 0)])
        _logger.info(">> Starting cron: calculate_remaining_period")
        for rec in records:
            _logger.info(f">> Processing record ID: {rec.id}")
            rec.used_period += 1
            rec.remaining_period = rec.period - rec.used_period