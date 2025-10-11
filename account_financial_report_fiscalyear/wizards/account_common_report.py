# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2021 (<http://www.exp-sa.com/>).
#
##############################################################################

from odoo import api, fields, models


class AbstractWizard(models.AbstractModel):
    _inherit = "account_financial_report_abstract_wizard"

    date_period_type = fields.Selection(
        string='Date Period Type',
        selection=[('fiscalyear', 'Fiscal Year'),
                   ('fiscalyear_period', 'Fiscal Year Period'), ])

    fiscalyear_id = fields.Many2one('account.fiscal.year',
                                    string='Fiscal Year',
                                    help='''The fiscalyear
                                used for this report.''')

    period_id = fields.Many2one('fiscalyears.periods',
                                string='Period',
                                help='''The fiscalyear period
                                used for this report.''')

    @api.onchange('fiscalyear_id')
    def _onchange_fiscalyear_id(self):
        if self.fiscalyear_id:
            if self.date_period_type == 'fiscalyear':
                self.date_from = self.fiscalyear_id.date_from
                self.date_to = self.fiscalyear_id.date_to

    @api.onchange('period_id')
    def _onchange_period_id(self):
        if self.period_id:
            if self.date_period_type == 'fiscalyear_period':
                self.date_from = self.period_id.date_from
                self.date_to = self.period_id.date_to
