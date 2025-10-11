# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from num2words import num2words


class CrossOveredBudgetPercentageWizard(models.TransientModel):
    _name = "crossovered.budget.percentage.wizard"
    _description = 'CrossOvered Budget Percentage Wizard'

    @api.model
    def default_get(self, fields):
        rec = super(CrossOveredBudgetPercentageWizard, self).default_get(fields)
        active_id = self._context.get('active_id')
        update = []
        if active_id:
            analytic_id = self.env['account.analytic.account'].browse(active_id)
            for line in analytic_id.crossovered_budget_line:
                update.append((0, 0, {
                    'budget_post_id': line.general_budget_id.id,
                }))
            rec.update({
                'line_ids': update
            })
        return rec

    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account",
                                          required=False, )

    line_ids = fields.One2many(comodel_name="crossovered.budget.percentage.line.wizard", inverse_name="wizard_id",
                               string="Lines", required=False, )

    def copy_lines(self):
        active_id = self._context.get('active_id')
        if active_id:
            analytic_id = self.env['account.analytic.account'].browse(active_id)
            new_analytic = analytic_id.copy()
            for line in analytic_id.crossovered_budget_line:
                planned_percentage = self.line_ids.filtered(
                    lambda row: row.budget_post_id.id == line.general_budget_id.id).percentage
                line.copy({
                    'analytic_account_id': new_analytic.id,
                    'planned_amount': line.practical_amount + ((planned_percentage / 100) * line.practical_amount),
                })
            return {
                'name': _('Analytic Accounts'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.analytic.account',
                'target': 'current',
                'res_id': new_analytic.id,
            }


class CrossOveredBudgetPercentageLineWizard(models.TransientModel):
    _name = "crossovered.budget.percentage.line.wizard"
    _description = 'CrossOvered Budget Percentage Lines Wizard'

    wizard_id = fields.Many2one(comodel_name="crossovered.budget.percentage.wizard", string="Wizard",
                                ondelete='cascade')

    budget_post_id = fields.Many2one(comodel_name="account.budget.post", string="Budgetary Position", required=False, )
    percentage = fields.Float(string="Percentage", required=False, )
