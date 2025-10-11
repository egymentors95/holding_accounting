from odoo import models, fields, api, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    is_analytic_budget = fields.Boolean(string="Is Use In Budget", default=False)
    is_auto_check = fields.Boolean(string="Auto Check", default=False)

#
# class CrossoveredBudgetLines(models.Model):
#     _inherit = "crossovered.budget.lines"
#
#     analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', domain=[('is_analytic_budget','=',True)])
