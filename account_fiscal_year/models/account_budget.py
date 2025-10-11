# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import  ValidationError, Warning


class CrossoveredBudget(models.Model):
    _name = "crossovered.budget"
    _inherit = "crossovered.budget"

    fiscalyear_id = fields.Many2one('account.fiscal.year',
                                    string='Fiscal Year', required=False, readonly=True,store=True,
                                    states={'draft': [('readonly', False)]},
                                    help='''The fiscalyear
                                used for this budget.''')

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        for budget in self:
            if budget.date_from and budget.date_to:
                fiscalyears = self.env['account.fiscal.year'].search(
                    [('state', '=', 'open'),
                     ('date_from', '<=', budget.date_from),
                     ('date_to', '>=', budget.date_to)])
                if fiscalyears:
                    budget.fiscalyear_id = fiscalyears[0].id
                else:
                    raise Warning(
                        _('''No fiscal year for
                         this budget date range.'''))

    @api.constrains('date_from', 'date_to', 'fiscalyear_id')
    def _check_dates_fiscalyear(self):
        ''' check date and fiscalyear_id
            are in the same date range
        '''
        for budget in self:
            if budget.date_from and budget.date_to and budget.fiscalyear_id:
                date_from = fields.Date.from_string(budget.date_from)
                date_to = fields.Date.from_string(budget.date_to)
                fiscalyear_start_date = fields.Date.from_string(
                    budget.fiscalyear_id.date_from)
                fiscalyear_end_date = fields.Date.from_string(
                    budget.fiscalyear_id.date_to)
                if not (date_from >= fiscalyear_start_date and
                        date_to <= fiscalyear_end_date):
                    raise ValidationError(
                        _('''Budget date range and fiscalyear must be in
                         the same'''))
            else:
                raise ValidationError(
                    _('''Budget date range must be within fiscalyear.'''))


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    fiscalyear_id = fields.Many2one('account.fiscal.year',
                                    related='crossovered_budget_id.fiscalyear_id',
                                    store=True, string='Period',
                                    related_sudo=False,
                                    help='''The fiscalyear
                                used for this budget line.''')
