# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class AssetRegisterReportXslx(models.AbstractModel):
    _name = 'report.report_asset_register_xlsx'
    _inherit = 'report.asset_abstract_report_xlsx'
    _description = 'report_asset_register_xlsx'

    def _get_report_name(self, report, data=False):
        return _('Asset Register')

    def _get_report_columns(self, report):
        return {
            0: {'header': 'RN',  'width': 5},
            1: {'header': 'Serial Number', 'width': 20},
            2: {'header': 'Asset Name', 'width': 20},
            3: {'header': 'Model Number', 'width': 14},
            4: {'header': 'Asset Location', 'width': 14},
            5: {'header': 'User', 'width': 14},
            6: {'header': 'Supplier', 'width': 14},
            7: {'header': 'Invoice Number', 'width': 20},
            8: {'header': 'Invoice Date', 'width': 12},
            9: {'header': 'Value', 'type': 'amount', 'width': 14},
            10: {'header': 'Received Date', 'width': 16},
            11: {'header': 'Warranty', 'width': 20},
            12: {'header': 'Registration Number', 'width': 20},
            13: {'header': 'Registration Date', 'width': 20},
            14: {'header': '# Existing Depreciation', 'width': 20},
            15: {'header': 'Existing Depreciation', 'width': 20},
            16: {'header': 'First Depreciation', 'width': 20},
            17: {'header': 'Depreciation %', 'width': 16},
            18: {'header': 'Up to Date', 'width': 12},
            19: {'header': 'Expired Days', 'width': 14},
            20: {'header': 'Depreciation', 'width': 14},
            21: {'header': 'Accumulated Depreciation', 'width': 20},
            22: {'header': 'Net Value', 'width': 14},
        }

    def _get_report_filters(self, report):
        return []

    def _get_col_count_filter_name(self):
        return 0

    def _get_col_count_filter_value(self):
        return 0

    def _generate_report_content(self, workbook, report, data, report_data):
        # For each asset
        seq = 1
        # Header
        report_data["sheet"].write(report_data["row_pos"], 0, "رقم", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 1, "رقم الأصل", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 2, "الاسم العلمي", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 3, "رقم التصنيع/الهيكل", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 4, "موقع الأصل", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 5, "المستخدم", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 6, "المورد", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 7, "رقم الفاتورة", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 8, "تاريخ الفاتورة", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 9, "القيمة", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 10, "تاريخ الإستلام", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 11, "تفاصيل الضمان", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 12, "رقم القيد", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 13, "تاريخ القيد", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 14, "عدد الاستهلاكات السابقة", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 15, "قيمة الاستهلاك السابق", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 16, "تاريخ اول اسستهلاك", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 17, "نسبة الاستهلاك", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 18, "تاريخ الاحتساب", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 19, "ايام الاستهلاك", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 20, "استهلاك السنة", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 21, "الاستهلاك التراكمي", report_data["formats"]["format_header_center"])
        report_data["sheet"].write(report_data["row_pos"], 22, "صافي القيمة الدفترية", report_data["formats"]["format_header_center"])
        report_data["row_pos"] += 1

        self.write_array_header(report_data)
        for asset in report:
            # Write asset line
            report_data["sheet"].write_number(report_data["row_pos"], 0, seq, report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 1, asset.serial_no or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 2, asset.name or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 3, asset.model or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 4, asset.location_id.name or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 5, asset.responsible_user_id.name or '', report_data["formats"]["format_center"])
            partner = []
            invoice = []
            for orginal_move in asset.original_move_line_ids:
                partner.append(orginal_move.partner_id.name)
                invoice.append(orginal_move.move_id.name)
            report_data["sheet"].write_string(report_data["row_pos"], 6, partner or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 7, invoice or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 8, asset.acquisition_date and asset.acquisition_date.strftime("%d/%m/%Y") or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_number(report_data["row_pos"], 9, float(asset.original_value), report_data["formats"]["format_amount"])
            report_data["sheet"].write_string(report_data["row_pos"], 10, asset.receive_date and asset.receive_date.strftime("%d/%m/%Y") or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 11, asset.warranty_contract or '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 12, '', report_data["formats"]["format_center"])
            report_data["sheet"].write_string(report_data["row_pos"], 13, '', report_data["formats"]["format_center"])

            report_data["sheet"].write_number(report_data["row_pos"], 14, asset.depreciation_number_import, report_data["formats"]["format_amount"])
            report_data["sheet"].write_number(report_data["row_pos"], 15, asset.already_depreciated_amount_import, report_data["formats"]["format_amount"])
            report_data["sheet"].write_string(report_data["row_pos"], 16, asset.first_depreciation_date_import and asset.first_depreciation_date_import.strftime("%d/%m/%Y") or '', report_data["formats"]["format_center"])

            percentage = 100/(asset.method_number*int(asset.method_period)/12)
            report_data["sheet"].write_number(report_data["row_pos"], 17, float(percentage), report_data["formats"]["format_amount"])

            posted_depreciation_move_ids = asset.depreciation_move_ids.filtered(
                lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id).sorted(
                key=lambda l: l.date)
            calc_date = posted_depreciation_move_ids[-1].date
            report_data["sheet"].write_string(report_data["row_pos"], 18, calc_date and calc_date.strftime("%d/%m/%Y") or '', report_data["formats"]["format_center"])
            first_dept = asset.first_depreciation_date_import or asset.receive_date or asset.date
            delta = calc_date and first_dept and calc_date-first_dept
            days = delta and delta.days or 0
            report_data["sheet"].write_number(report_data["row_pos"], 19, float(days), report_data["formats"]["format_amount"])
            report_data["sheet"].write_number(report_data["row_pos"], 20, float((asset.original_value-asset.already_depreciated_amount_import)*percentage/100), report_data["formats"]["format_amount"])
            report_data["sheet"].write_number(report_data["row_pos"], 21, float(asset.original_value-asset.value_residual), report_data["formats"]["format_amount"])
            report_data["sheet"].write_number(report_data["row_pos"], 22, float(asset.book_value), report_data["formats"]["format_amount"])
            seq += 1
            report_data["row_pos"] += 1

