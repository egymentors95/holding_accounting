# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from dateutil.rrule import rrule, MONTHLY
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

class AssetDepreciationReportXslx(models.AbstractModel):
    _name = 'report.asset_depreciation_report_xlsx'
    _inherit = 'report.asset_abstract_report_xlsx'
    _description = 'asset_depreciation_report_xlsx'

    def _get_report_name(self, report):
        return _('Fixed Asset Register')

    def _get_report_columns(self, report):
        return {
            0: {'width': 5},
            1: {'width': 12},
            2: {'width': 20},
            3: {'width': 12},
            4: {'width': 12},
            5: {'width': 12},
            6: {'width': 12},
            7: {'width': 12},
            8: {'width': 12},
            9: {'width': 12},
            10: {'width': 12},
            11: {'width': 12},
            12: {'width': 12},
            13: {'width': 12},
            14: {'width': 12},
            15: {'width': 12},
            16: {'width': 12},
            17: {'width': 12},
            18: {'width': 12},
            19: {'width': 12},
        }

    def _get_report_filters(self, report):
        return [
            [
                _('Duration'), _('From: ') + report.start_date + '    ' + _('To: ') + report.end_date
            ],
            [
                _('Categories'), ', '.join([c.name for c in report.category_ids]),
            ],
        ]

    def _get_col_count_filter_name(self):
        return 1

    def _get_col_count_filter_value(self):
        return 3

    def _generate_report_content(self, workbook, report):
        # For each category
        depreciation_line = self.env['account.asset.depreciation.line']

        start_date = datetime.strptime(report.start_date, DF)
        end_date = datetime.strptime(report.end_date, DF)
        periods = [dt.strftime("%b-%y") for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]

        seq = 1
        depreciation_register = self.env['report_asset_register_depreciation']
        for category in report.category_ids:
            # Write category info
            self.sheet.write(self.row_pos, 0, seq, self.format_header1)
            self.sheet.merge_range(self.row_pos, 1, self.row_pos, 2, category.name, self.format_header1)
            percentage = 100/(category.method_number*category.method_period/12)
            self.sheet.write(self.row_pos, 3, str(round(percentage,2))+"%", self.format_header1)
            self.sheet.write(self.row_pos, 4, "", self.format_header1)
            self.sheet.merge_range(self.row_pos, 5, self.row_pos, 4+len(periods), "DEPRECIATION BY MONTH", self.format_header1)
            self.sheet.write(self.row_pos, 5+len(periods), "Depr'n.", self.format_header1)
            self.sheet.write(self.row_pos, 6+len(periods), "Accu Deprn.", self.format_header1)
            self.sheet.write(self.row_pos, 7+len(periods), "NBV", self.format_header1)
            self.row_pos += 1

            #Write Header
            self.sheet.write(self.row_pos, 0, "", self.format_header2)
            self.sheet.write(self.row_pos, 1, "Date", self.format_header2)
            self.sheet.write(self.row_pos, 2, "Description of Asset", self.format_header2)
            self.sheet.write(self.row_pos, 3, "Ref. Doc.", self.format_header2)
            self.sheet.write(self.row_pos, 4, "Amount", self.format_header2)
            column_pos = 4
            for p in periods:
                column_pos += 1
                self.sheet.write(self.row_pos, column_pos, p, self.format_header2)
            self.sheet.write(self.row_pos, column_pos+1, report.start_date+'-'+report.end_date, self.format_header2)
            self.sheet.write(self.row_pos, column_pos+2, report.end_date, self.format_header2)
            self.sheet.write(self.row_pos, column_pos+3, 'After '+report.end_date, self.format_header2)
            self.row_pos += 1

            #Write Asset
            asset_ids = self.env['account.asset'].search([('category_id', '=', category.id),
                                                                ('date', '<=', report.end_date)])
            for asset in asset_ids:

                self.sheet.write(self.row_pos, 0, "", self.format_center)
                self.sheet.write(self.row_pos, 1, asset.date, self.format_center)
                self.sheet.write(self.row_pos, 2, asset.name, self.format_center)
                self.sheet.write(self.row_pos, 3, asset.invoice_id.name, self.format_center)
                self.sheet.write(self.row_pos, 4, asset.value, self.format_center)

                column_pos = 4
                fy_depreciation = 0
                for p in periods:
                    column_pos += 1
                    depreciation = depreciation_register.search([('report_id', '=', report.id),
                                                                 ('asset_id', '=', asset.id),
                                                                 ('period', '=', p)])
                    amount = sum([d.amount for d in depreciation])
                    fy_depreciation += amount
                    self.sheet.write(self.row_pos, column_pos, amount, self.format_center)
                self.sheet.write(self.row_pos, column_pos+1, fy_depreciation, self.format_center)
                accu = depreciation_line.read_group([('depreciation_date', '<=', report.end_date),
                                                     ('asset_id','=', asset.id)],
                                                    ['asset_id', 'amount'], ['asset_id'])
                accu_depreciation = accu and accu[0].get('amount') or 0
                self.sheet.write(self.row_pos, column_pos+2, accu_depreciation, self.format_center)
                self.sheet.write(self.row_pos, column_pos+3, asset.value - accu_depreciation, self.format_center)
                self.row_pos += 1
            seq += 1
            self.row_pos += 1

