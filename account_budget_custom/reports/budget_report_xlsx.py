# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, api, _
from odoo.exceptions import ValidationError


class ReportSponsorPdf(models.AbstractModel):
    _name = 'report.account_budget_custom.budget_report'
    _description = 'Budget Report'

    @api.model
    def get_report_values(self, docids, data=None):
        docs = []
        title = _("Budget Lines")
        release_date = datetime.now().date()
        seq = self.env['ir.actions.report'].get_report_sequence('account_budget_custom.budget_report')['seq']

        lines = self.env['crossovered.budget.lines'].search([('id', 'in', data['records'])])
        for i in lines:
            docs.append({
                'crossovered_budget_id': i.crossovered_budget_id.id,
                'general_budget_id': i.general_budget_id.id,
                'date_from': datetime.strptime(i.date_from, '%Y-%m-%d %H:%M:%S').date(),
                'date_to': datetime.strptime(i.date_to, '%Y-%m-%d %H:%M:%S').date(),
                'planned_amount': i.planned_amount,
                'practical_amount': i.practical_amount,
                'theoritical_amount': i.theoritical_amount,
                'percentage': i.percentage
            })

        if docs:
            return {
                'doc_ids': docids,
                'doc_model': self.env['crossovered.budget.lines'],
                'date': release_date,
                'seq': seq,
                'title': title,
                'docs': docs,
            }
        else:
            raise ValidationError(_("Sorry, No data to Print"))

    def get_result(self, data=None):
        res = []
        labels = [
            [_("المـوازنـة"), _("وضع المـوازنـة"), _("تاريخ البدء"), _("تاريخ الإنتهاء"), _("المبلغ المخطط"),
             _("المبلغ الفعلى"), _("المبلغ النظرية"), _("الإنجاز")]]

        budget_lines = self.env['crossovered.budget.lines'].search([])
        for i in budget_lines:
            res.append({
                'crossovered_budget_id': i.crossovered_budget_id.name,
                'general_budget_id': i.general_budget_id.name,
                'date_from': i.date_from,
                'date_to': i.date_to,
                'planned_amount': i.planned_amount,
                'practical_amount': i.practical_amount,
                'theoritical_amount': i.theoritical_amount,
                'percentage': i.percentage,
                'labels': labels
            })
        return res


class InstitutionXlsxReport(models.AbstractModel):
    _name = 'report.account_budget_custom.budget_xslx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Budget XLSX Report'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        docs = self.env['report.account_budget_custom.budget_report'].get_result(data)
        if docs:
            title = _("الموازنات")
            sheet = workbook.add_worksheet('الموازنات')
            sheet.right_to_left()
            format1 = workbook.add_format(
                {'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center', })
            format2 = workbook.add_format(
                {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
                 'bold': True})
            format5 = workbook.add_format(
                {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
                 'bold': True, 'fg_color': '#dcdcdc'})
            format2.set_align('center')
            sheet.set_column('C:L', 15)
            row = 10
            i, n, c = 1, 1, 1
            for line in docs:
                clm = 2
                for le in line['labels'][0]:
                    if i > 1:
                        break
                    else:
                        clm += 1
                        sheet.write(row, clm, le, format5)
                        c += 1
                i += 1
                row += 1
                clm = 2
                sheet.write(row, clm + 1, line['crossovered_budget_id'], format1)
                sheet.write(row, clm + 2, line['general_budget_id'], format1)
                sheet.write(row, clm + 3, line['date_from'], format1)
                sheet.write(row, clm + 4, line['date_to'], format1)
                sheet.write(row, clm + 5, line['planned_amount'], format1)
                sheet.write(row, clm + 6, line['practical_amount'], format1)
                sheet.write(row, clm + 7, line['theoritical_amount'], format1)
                sheet.write(row, clm + 8, line['percentage'], format1)

                n += 1
