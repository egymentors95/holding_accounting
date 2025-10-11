# © 2016 Julien Coux (Camptocamp)
# © 2018 Forest and Biomass Romania SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from dateutil.rrule import rrule, MONTHLY
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta

class AssetRegisterReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * AssetRegisterReport
    ** Asset Category
    ***  Asset
    **** AssetRegisterReportDepreciation
    """
    _name = 'report_asset_register'

    # Filters fields, used for data computation
    category_ids = fields.Many2many('account.asset.category')
    start_date = fields.Date()
    end_date = fields.Date()
    depreciation_ids = fields.One2many('report_asset_register_depreciation', 'report_id')

    @api.one
    def compute_data_for_report(self):
        self.depreciation_ids.unlink()
        depreciation = self.env['account.asset.depreciation.line']
        depreciation_register = self.env['report_asset_register_depreciation']
        asset = self.env['account.asset'].search([('category_id', 'in', self.category_ids.ids),
                                                        ('date', '<=', self.end_date)])
        start_date = datetime.strptime(self.start_date, DF).replace(day=1)
        end_date = datetime.strptime(self.end_date, DF) + timedelta(days=1)
        dates = [dt for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]
        dates[0] = datetime.strptime(self.start_date, DF)

        for p in range(0, len(dates)):
            start = dates[p]
            end = p != len(dates)-1 and dates[p+1] or end_date
            line = depreciation.search([('depreciation_date', '>=', start.strftime(DF)),
                                        ('depreciation_date', '<', end.strftime(DF)),
                                        ('asset_id', 'in', asset.ids),
                                        ('move_id', '!=', False)])
            for l in line:
                val = {
                    'report_id': self.id,
                    'asset_id': l.asset_id.id,
                    'period': start.strftime("%b-%y"),
                    'amount': l.amount,
                    'date': l.depreciation_date,

                }
                depreciation_register.create(val)

    @api.multi
    def print_report(self):
        self.ensure_one()
        return self.env['ir.actions.report'].search(
            [('report_name', '=', 'asset_depreciation_report_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1).report_action(self)


class AssetRegisterReportDepreciation(models.TransientModel):
    _name = 'report_asset_register_depreciation'

    report_id = fields.Many2one('report_asset_register', ondelete='cascade', index=True)
    asset_id = fields.Many2one('account.asset')
    period = fields.Char()
    amount = fields.Float()
    date = fields.Date()

