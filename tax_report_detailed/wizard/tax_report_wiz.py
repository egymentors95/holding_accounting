from odoo import models, fields, api, _
from datetime import datetime, date


class TaxReportWiz(models.TransientModel):
    _name = 'tax.report.wiz'
    _description = 'Tax Report Wiz'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    date_period_type = fields.Selection(
        string='Date Period Type',
        selection=[('fiscalyear', 'Fiscal Year'),
                   ('fiscalyear_period', 'Fiscal Year Period'), ])

    fiscalyear_id = fields.Many2one('account.fiscal.year',
                                    string='Fiscal Year',
                                    help='''The fiscalyear used for this report.''')

    period_id = fields.Many2one('fiscalyears.periods',
                                string='Period',
                                help='''The fiscalyear period used for this report.''')

    government_type = fields.Selection(string="Governmental Type",
                                       selection=[('gov', 'Governmental'), ('not_gov', 'Non-Governmental'), ],
                                       required=False, )

    @api.onchange('date_period_type', 'fiscalyear_id')
    def _onchange_fiscalyear_id(self):
        if self.fiscalyear_id:
            if self.date_period_type == 'fiscalyear':
                self.date_from = self.fiscalyear_id.date_from
                self.date_to = self.fiscalyear_id.date_to
            return {'domain': {'period_id': [('fiscalyear_id', '=', self.fiscalyear_id.id)]}}

    @api.onchange('date_period_type', 'period_id')
    def _onchange_period_id(self):
        if self.period_id:
            if self.date_period_type == 'fiscalyear_period':
                self.date_from = self.period_id.date_from
                self.date_to = self.period_id.date_to

    def print_report(self):
        data = {}
        res = self.read()
        res = res and res[0] or {}
        data.update({'form': res})
        return self.env.ref('tax_report_detailed.report_tax_details_xlsx').report_action(self, data=data)

    def compute_table_data(self):

        date_to_start = date(datetime.now().date().year, 1, 1)
        date_to_print = date(datetime.now().date().year, 12, 31)
        date_from = self.date_from or str(date_to_start)
        date_to = self.date_to or str(date_to_print)
        self.env.cr.execute("TRUNCATE tax_report_details RESTART IDENTITY CASCADE;")
        self.env['tax.report.details'].refresh()
        tax_details = self.env['report.tax_report_detailed.report_tax_details_xlsx']
        report = self.env['tax.report.details']
        for invoice in tax_details.invoice_tax(date_from, date_to, self.government_type):
            report.create(invoice)

        modules = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
                                                              ('name', '=', 'hr_expense_petty_cash')])
        if modules:
            for petty in tax_details.petty_tax(date_from, date_to, self.government_type):
                report.create(petty)

        modules = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
                                                              ('name', '=', 'point_of_sale')])
        if modules:
            for pos in tax_details.pos_order_tax(date_from, date_to, self.government_type):
                report.create(pos)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Tax Details'),
            'res_model': 'tax.report.details',
            'view_mode': 'tree,form',
            'context': {'search_default_group_type': 1, 'search_default_group_tax': 1}
        }
