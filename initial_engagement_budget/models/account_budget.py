# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    initial_engagement_amount = fields.Float(string='Initial Engagement', compute='_compute_initial_engagement_amount',
                                             help=_(
                                                 'Total amount of confirmed purchase requests for this budget line.'))
    remain = fields.Float(string='Remain of Christening', compute='_compute_remain_new',
                          help=_('Amount of money that has been remained'))
    above_remain = fields.Float(string='Exceed Amount', compute='_compute_remain_new',
                                help=_('Amount of money that has been exceeded'))

    @api.depends('to_operation_ids', 'from_operation_ids')
    def _compute_remain_new(self):
        for line in self:
            remain_value = ((abs(line.final_amount) - abs(line.reserve) - abs(line.confirm) - abs(
                line.practical_amount)- abs(line.initial_engagement_amount)) * -1)
            line.remain = 0 if remain_value > 0 else remain_value
            line.above_remain = remain_value if remain_value > 0 else 0

    @api.depends('analytic_account_id')
    def _compute_initial_engagement_amount(self) -> None:
        for rec in self:
            rec.initial_engagement_amount = sum(
                self.env['budget.confirmation.line'].search([('confirmation_id.state', '=', 'done'),
                                                             ('confirmation_id.request_id.state', '!=', 'done'),
                                                             ('confirmation_id.request_id.purchase_create', '!=', True),
                                                             ('confirmation_id.type', '=',
                                                              'purchase.request'),
                                                             ('account_id', 'in',
                                                              rec.general_budget_id.account_ids.ids),
                                                             ('analytic_account_id', '=',
                                                              rec.analytic_account_id.id)]).mapped(
                    'amount'))
