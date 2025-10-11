# -*- coding: utf-8 -*-

from odoo import models
from datetime import datetime, date
import itertools
import operator


class TaxDetailsXlsx(models.AbstractModel):
    _name = 'report.tax_report_detailed.report_tax_details_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Tax Details xlsx'

    def generate_xlsx_report(self, workbook, data, taxes):
        date_to_start = date(datetime.now().date().year, 1, 1)
        date_to_print = date(datetime.now().date().year, 12, 31)
        date_from = data['form'].get('date_from', ) or str(date_to_start)
        date_to = data['form'].get('date_to', ) or str(date_to_print)
        government_type = data['form'].get('government_type', 'False')
        tax_lines = self.invoice_tax(date_from, date_to, government_type)

        modules = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
                                                              ('name', '=', 'hr_expense_petty_cash')])
        if modules:
            tax_lines += self.petty_tax(date_from, date_to, government_type)

        modules = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
                                                              ('name', '=', 'point_of_sale')])
        if modules:
            tax_lines += self.pos_order_tax(date_from, date_to, government_type)

        self.report_generation(workbook, date_from, date_to, tax_lines)

    def invoice_tax(self, date_from, date_to, government_type=False):
        domain = [
            ('move_id.invoice_date', '<=', date_to),
            ('move_id.invoice_date', '>=', date_from),
            ('move_id.state', 'not in', ['draft', 'cancel']),
            ('tax_ids', '!=', False),
        ]
        if government_type:
            domain.append(('tax_ids.government_type', '=', government_type))
        taxed_lines = self.env['account.move.line'].search(domain)
        tax_grouped = {}
        for line in taxed_lines:
            for tax in line.tax_ids:
                taxes = \
                    tax.compute_all(line.price_unit, line.currency_id, line.quantity,
                                    line.product_id, line.partner_id)['taxes']

                key = 'inv,%s-%s' % (line.move_id.id, tax.id)
                for t in taxes:
                    print(line.product_id.name, 'line.produ11111,,,,,,,,,,,,,')
                    if key not in tax_grouped:
                        tax_grouped[key] = {
                            'num': line.move_id.name,
                            # 'desc': line.product_id.name,
                            'date': line.move_id.invoice_date,
                            'tax_id': tax.id,
                            'tax_name': tax.name,
                            'record_type': (line.move_id.move_type in ['in_invoice', 'in_receipt'] and 'purchase') or (
                                    line.move_id.move_type in ['out_invoice',
                                                               'out_receipt'] and 'sale') or line.move_id.move_type,
                            'vat': line.partner_id.vat,
                            'partner_id': line.partner_id.id,
                            'partner_name': line.partner_id.name,
                            'amount_exclude': t.get('base', 0),
                            'amount_tax': t.get('amount', 0),
                            'total_amount': t.get('base', 0) + t.get('amount', 0)
                        }
                    else:
                        tax_grouped[key]['amount_exclude'] += t.get('base', 0)
                        tax_grouped[key]['amount_tax'] += t.get('amount', 0)
                        tax_grouped[key]['total_amount'] += t.get('base', 0) + t.get('amount', 0)
        print(list(tax_grouped.values()), 'list(tax_grouped.values())')
        return list(tax_grouped.values())

    def petty_tax(self, date_from, date_to, government_type=False):
        domain = [('accounting_date', '<=', date_to),
                  ('accounting_date', '>=', date_from),
                  ('state', '=', 'done'),
                  ('tax_ids', '!=', False),
                  ]
        if government_type:
            domain.append(('tax_ids.government_type', '=', government_type))
        taxed_lines = self.env['hr.expense'].search(domain)

        tax_grouped = {}
        for line in taxed_lines:
            for tax in line.tax_ids:
                taxes = \
                    tax.compute_all(line.unit_amount, line.currency_id, line.quantity,
                                    line.product_id, line.partner_id)['taxes']

                key = 'petty,%s-%s' % (line.reference, tax.id)
                for t in taxes:
                    if key not in tax_grouped:
                        tax_grouped[key] = {
                            'num': line.reference,
                            # 'desc': line.product_id.name,
                            'date': line.accounting_date,
                            'tax_id': tax.id,
                            'tax_name': tax.name,
                            'record_type': 'purchase',
                            'vat': line.vat,
                            'partner_id': line.partner_id.id,
                            'partner_name': line.partner_id.name,
                            'amount_exclude': t.get('base', 0),
                            'amount_tax': t.get('amount', 0),
                            'total_amount': t.get('base', 0) + t.get('amount', 0)
                        }
                    else:
                        tax_grouped[key]['amount_exclude'] += t.get('base', 0)
                        tax_grouped[key]['amount_tax'] += t.get('amount', 0)
                        tax_grouped[key]['total_amount'] += t.get('base', 0) + t.get('amount', 0)

        return list(tax_grouped.values())

    def pos_order_tax(self, date_from, date_to, government_type):
        domain = [('order_id.date_order', '<=', date_to),
                  ('order_id.date_order', '>=', date_from),
                  ('order_id.state', 'not in', ['draft', 'cancel']),
                  ('tax_ids', '!=', False)]
        if government_type:
            domain.append(('tax_ids.government_type', '=', government_type))
        taxed_lines = self.env['pos.order.line'].search(domain)

        tax_grouped = {}
        for line in taxed_lines:
            for tax in line.tax_ids:
                taxes = \
                    tax.compute_all(line.price_unit, line.order_id.pricelist_id.currency_id, line.qty,
                                    line.product_id, line.order_id.partner_id)['taxes']

                key = 'pos,%s-%s' % (line.order_id.id, tax.id)
                for t in taxes:
                    if key not in tax_grouped:
                        tax_grouped[key] = {
                            'num': line.order_id.name,
                            # 'desc': line.product_id.name,
                            'date': line.order_id.date_order,
                            'tax_id': tax.id,
                            'tax_name': tax.name,
                            'record_type': t.get('amount', 0) >= 0 and 'sale' or 'out_refund',
                            'vat': line.order_id.partner_id.vat,
                            'partner_id': line.order_id.partner_id.id,
                            'partner_name': line.order_id.partner_id.name,
                            'amount_exclude': t.get('base', 0),
                            'amount_tax': t.get('amount', 0),
                            'total_amount': t.get('base', 0) + t.get('amount', 0)
                        }
                    else:
                        tax_grouped[key]['amount_exclude'] += t.get('base', 0)
                        tax_grouped[key]['amount_tax'] += t.get('amount', 0)
                        tax_grouped[key]['total_amount'] += t.get('base', 0) + t.get('amount', 0)
        return list(tax_grouped.values())

    def report_generation(self, workbook, date_from, date_to, tax_lines):
        company_header = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vleft',
            'text_wrap': True,
            'bg_color': 'white',
        })
        company_header2 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vleft',
            'text_wrap': True,
            'font_color': '#843c0b',
            'bg_color': 'white',
        })
        # Table Header
        header_format1 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#c5e0b4',
        })
        header_format2 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#dae3f3',
        })  # Table Total
        total_format1 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_color': '#843c0b',
            'bg_color': '#e2f0d9',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        total_format2 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_color': '#843c0b',
            'bg_color': '#deebf7',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        total_format3 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#fff2cc',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        lines_format1 = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#e2f0d9',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        lines_format2 = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#deebf7',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        lines_format3 = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#fff2cc',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        item_format1 = workbook.add_format({
            'border': 1,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_color': 'white',
            'bg_color': '#548235',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        vat_format1 = workbook.add_format({
            'border': 1,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_color': 'white',
            'bg_color': '#548235',
        })
        vat_format1.set_rotation(90)
        vat_format2 = workbook.add_format({
            'border': 1,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_color': 'white',
            'bg_color': '#2e75b6',
        })
        vat_format2.set_rotation(90)
        vat_format3 = workbook.add_format({
            'border': 1,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_color': 'white',
            'bg_color': '#c55a11',
        })
        vat_format3.set_rotation(90)
        lines_format4 = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': 'white',
            'num_format': '#,##0.00_);(#,##0.00)',
        })
        total_sheet = workbook.add_worksheet('VAT Return')
        total_sheet.hide_gridlines(2)
        total_sheet.set_default_row(25)
        total_sheet.set_row(0, 35)
        total_sheet.merge_range('A1:C1', 'Entity Name: ', company_header)
        total_sheet.merge_range('D1:E1', self.env.user.company_id.name, company_header2)

        total_sheet.merge_range('A2:C2', 'Vat registration Number الرقم الضريبي: ', company_header)
        total_sheet.merge_range('D2:E2', self.env.user.company_id.vat or '', company_header2)

        total_sheet.merge_range('A3:C3', 'Month End : ', company_header)
        total_sheet.merge_range('D3:E3', str(date_to), company_header2)

        total_sheet.set_column(1, 7, 20)
        total_sheet.merge_range('A4:D5', 'ضريبة قيمة مضافة على المبيعات', header_format1)
        total_sheet.merge_range('E4:E5', 'Amount Exclusive of Vat المبلغ', header_format1)
        total_sheet.merge_range('F4:F5', 'Adjustments التعديل', header_format1)
        total_sheet.merge_range('G4:G5', 'مبلغ الضريبة Vat Amount', header_format1)

        grouped_list = []
        for d, f in itertools.groupby(sorted(tax_lines, key=operator.itemgetter('tax_id')),
                                      key=operator.itemgetter('tax_id')):
            vals_total = {'tax_id': d, 'values': list(f)}
            grouped_list.append(vals_total)

        sale_purchase_list = {'sale': [], 'purchase': []}

        for item in grouped_list:
            item_name = self.env['account.tax'].browse(item.get('tax_id')).name
            try:
                item_sheet = workbook.add_worksheet(item_name)
            except Exception:
                item_sheet = workbook.add_worksheet(item_name + '_%s' % item.get('tax_id'))
            item_sheet.hide_gridlines(2)
            item_sheet.set_default_row(25)
            item_sheet.set_column(0, 2, 18)
            item_sheet.set_column(3, 4, 25)
            item_sheet.set_column(5, 5, 30)
            item_sheet.set_column(6, 9, 18)

            item_sheet.set_row(5, 50)

            item_sheet.merge_range('A1:C1', 'Entity Name: ', company_header)
            item_sheet.merge_range('D1:E1', self.env.user.company_id.name, company_header2)

            item_sheet.merge_range('A2:C2', 'Vat registration Number الرقم الضريبي: ', company_header)
            item_sheet.merge_range('D2:E2', self.env.user.company_id.vat or '', company_header2)

            item_sheet.merge_range('A3:C3', 'Month End : ', company_header)
            item_sheet.merge_range('D3:E3', str(date_to), company_header2)

            item_sheet.merge_range('A5:E5', item_name, company_header)
            item_sheet.write(5, 0, 'Invoice No رقم الفاتورة ', item_format1)
            item_sheet.write(5, 1, 'Date التاريخ ', item_format1)
            item_sheet.write(5, 2, 'Customer name العميل ', item_format1)
            item_sheet.write(5, 3, 'Customer VAT Registration # (If any) الرقم الضريبي ', item_format1)
            # item_sheet.write(5, 4, 'Explanation البيان ', item_format1)
            item_sheet.write(5, 4, 'Amount exclusive of VAT المبالغ الخاضعة للضريبة الأساسية ',
                             item_format1)
            item_sheet.write(5, 5, 'VAT Amount قيمة الضريبة ', item_format1)
            item_sheet.write(5, 6, 'Total إجمالي ', item_format1)
            item_sheet.write(5, 7, 'ملاحظات Remarks', item_format1)
            row = 6
            sale_amount_exclude = 0
            sale_amount_tax = 0
            sale_adjustment = 0
            purchase_amount_exclude = 0
            purchase_amount_tax = 0
            purchase_adjustment = 0

            # Sale & Purchase Details
            for record in filter(lambda x: x.get('record_type') in ['sale', 'purchase'], item['values']):
                item_sheet.write(row, 0, record.get('num'), lines_format4)
                item_sheet.write(row, 1, str(record.get('date')), lines_format4)
                item_sheet.write(row, 2, record.get('partner_name'), lines_format4)
                item_sheet.write(row, 3, record.get('vat'), lines_format4)
                # item_sheet.write(row, 4, record.get('desc'), lines_format4)
                item_sheet.write(row, 4, record.get('amount_exclude'), lines_format4)
                item_sheet.write(row, 5, record.get('amount_tax'), lines_format4)
                item_sheet.write(row, 6, record.get('total_amount'), lines_format4)
                item_sheet.write(row, 7, '', lines_format4)
                row += 1
                if record.get('record_type') == 'sale':
                    sale_amount_exclude += record.get('amount_exclude')
                    sale_amount_tax += record.get('amount_tax')
                elif record.get('record_type') == 'purchase':
                    purchase_amount_exclude += record.get('amount_exclude')
                    purchase_amount_tax += record.get('amount_tax')
            item_sheet.merge_range(row, 0, row, 4, 'Total إجمالي ', item_format1)
            item_sheet.write(row, 4, sale_amount_exclude + purchase_amount_exclude, item_format1)
            item_sheet.write(row, 5, sale_amount_tax + purchase_amount_tax, item_format1)
            item_sheet.write(row, 6,
                             sale_amount_exclude + purchase_amount_exclude + sale_amount_tax + purchase_amount_tax,
                             item_format1)
            item_sheet.write(row, 7, '', item_format1)
            row += 2

            # Adjustment Details
            item_sheet.merge_range(row, 0, row, 4, 'Adjustments التعديلات', company_header)
            row += 1
            item_sheet.set_row(row, 50)
            item_sheet.write(row, 0, 'Invoice No رقم الفاتورة ', item_format1)
            item_sheet.write(row, 1, 'Date التاريخ ', item_format1)
            item_sheet.write(row, 2, 'Customer name العميل ', item_format1)
            item_sheet.write(row, 3, 'Customer VAT Registration # (If any) الرقم الضريبي ', item_format1)
            # item_sheet.write(row, 4, 'Explanation البيان ', item_format1)
            item_sheet.write(row, 4, 'Amount exclusive of VAT المبالغ الخاضعة للضريبة الأساسية ',
                             item_format1)
            item_sheet.write(row, 5, 'VAT Amount قيمة الضريبة ', item_format1)
            item_sheet.write(row, 6, 'Total إجمالي ', item_format1)
            item_sheet.write(row, 7, 'ملاحظات Remarks', item_format1)
            row += 1
            total_exclude = 0
            for record in filter(lambda x: x.get('record_type') in ['out_refund', 'in_refund'], item['values']):
                item_sheet.write(row, 0, record.get('num'), lines_format4)
                item_sheet.write(row, 1, str(record.get('date')), lines_format4)
                item_sheet.write(row, 2, record.get('partner_name'), lines_format4)
                item_sheet.write(row, 3, record.get('vat'), lines_format4)
                # item_sheet.write(row, 4, record.get('desc'), lines_format4)
                item_sheet.write(row, 4, record.get('amount_exclude'), lines_format4)
                item_sheet.write(row, 5, record.get('amount_tax'), lines_format4)
                item_sheet.write(row, 6, record.get('total_amount'), lines_format4)
                item_sheet.write(row, 7, '', lines_format4)
                row += 1
                total_exclude += record.get('amount_exclude')
                if record.get('record_type') == 'out_refund':
                    sale_adjustment += record.get('amount_tax')
                elif record.get('record_type') == 'in_refund':
                    purchase_adjustment += record.get('amount_tax')

            item_sheet.merge_range(row, 0, row, 4, 'Total إجمالي ', item_format1)
            item_sheet.write(row, 4, total_exclude, item_format1)
            item_sheet.write(row, 5, sale_adjustment + purchase_adjustment, item_format1)
            item_sheet.write(row, 6, total_exclude + sale_adjustment + purchase_adjustment, item_format1)
            item_sheet.write(row, 7, '', item_format1)

            if sale_amount_exclude > 0 or sale_amount_tax > 0 or sale_adjustment > 0:
                sale_purchase_list['sale'] += [{'tax_name': item_name,
                                                'amount_exclude': sale_amount_exclude,
                                                'amount_adjustment': sale_adjustment,
                                                'amount_tax': sale_amount_tax}]

            if purchase_amount_exclude > 0 or purchase_amount_tax > 0 or purchase_adjustment > 0:
                sale_purchase_list['purchase'] += [{'tax_name': item_name,
                                                    'amount_exclude': purchase_amount_exclude,
                                                    'amount_adjustment': purchase_adjustment,
                                                    'amount_tax': purchase_amount_tax}]
        # Total Sheet
        column = 6
        start_value = 6
        sale_total_exclude = 0
        sale_total_adjustment = 0
        sale_total_tax = 0
        for sale_item in sale_purchase_list['sale']:
            total_sheet.merge_range('B%s:D%s' % (column, column),
                                    sale_item.get('tax_name') or 'Undefiend',
                                    lines_format1)
            total_sheet.write('E%s' % (column), sale_item.get('amount_exclude'), lines_format1)
            total_sheet.write('F%s' % (column), sale_item.get('amount_adjustment'), lines_format1)
            total_sheet.write('G%s' % (column), sale_item.get('amount_tax'), lines_format1)
            sale_total_exclude += sale_item.get('amount_exclude')
            sale_total_adjustment += sale_item.get('amount_adjustment')
            sale_total_tax += sale_item.get('amount_tax')
            column += 1
        total_sheet.set_row(column, 30)
        total_sheet.merge_range('A%s:A%s' % (start_value, column + 1), 'Vat On Sales', vat_format1)
        total_sheet.merge_range('B%s:D%s' % (column, column), 'Total Sales إجمالي المبيعات', total_format1)
        total_sheet.write('E%s' % (column), sale_total_exclude, total_format1)
        total_sheet.write('F%s' % (column), sale_total_adjustment, total_format1)
        total_sheet.write('G%s' % (column), sale_total_tax, total_format1)
        column += 1
        total_sheet.merge_range('B%s:F%s' % (column, column), 'Net Sales Tax صافي ضريبة المبيعات', total_format1)
        total_sheet.write('G%s' % (column), sale_total_tax - sale_total_adjustment, total_format1)
        column += 1
        total_sheet.merge_range('A%s:D%s' % (column, column + 1), 'ضريبة قيمة مضافة على المشتريات', header_format2)
        total_sheet.merge_range('E%s:E%s' % (column, column + 1), 'Amount Exclusive of Vat المبلغ', header_format2)
        total_sheet.merge_range('F%s:F%s' % (column, column + 1), 'Adjustments التعديل', header_format2)
        total_sheet.merge_range('G%s:G%s' % (column, column + 1), 'مبلغ الضريبة Vat Amount', header_format2)
        column += 2
        startp_value = column
        purchase_total_exclude = 0
        purchase_total_adjustment = 0
        purchase_total_tax = 0
        for purhcase_item in sale_purchase_list['purchase']:
            total_sheet.merge_range('B%s:D%s' % (column, column), '', lines_format2)
            total_sheet.write('B%s' % (column), purhcase_item.get('tax_name') or 'Undefiend',
                              lines_format2)
            total_sheet.write('E%s' % (column), purhcase_item.get('amount_exclude'), lines_format2)
            total_sheet.write('F%s' % (column), purhcase_item.get('amount_adjustment'), lines_format2)
            total_sheet.write('G%s' % (column), purhcase_item.get('amount_tax'), lines_format2)
            purchase_total_exclude += purhcase_item.get('amount_exclude')
            purchase_total_adjustment += purhcase_item.get('amount_adjustment')
            purchase_total_tax += purhcase_item.get('amount_tax')
            column += 1
        total_sheet.set_row(column, 30)
        total_sheet.merge_range('A%s:A%s' % (startp_value, column + 1), 'Vat On Purchase', vat_format2)
        total_sheet.merge_range('B%s:D%s' % (column, column), 'Total Purchase إجمالي المشتريات', total_format2)
        total_sheet.write('E%s' % (column), purchase_total_exclude, total_format2)
        total_sheet.write('F%s' % (column), purchase_total_adjustment, total_format2)
        total_sheet.write('G%s' % (column), purchase_total_tax, total_format2)
        column += 1
        total_sheet.merge_range('B%s:F%s' % (column, column), 'Net Purchase Tax صافي ضريبة المشتريات', total_format2)
        total_sheet.write('G%s' % (column), purchase_total_tax - purchase_total_adjustment, total_format2)
        column += 1
        startf_value = column
        total_sheet.merge_range('B%s:F%s' % (column, column),
                                'Total Vat due to current period اجمالي ضريبة القيمة المضافة المستحقة للفترة',
                                lines_format3)
        total_sheet.write('G%s' % (column), (
                sale_total_tax - sale_total_adjustment) - (purchase_total_tax - purchase_total_adjustment),
                          lines_format3)
        column += 1
        total_sheet.merge_range('B%s:F%s' % (column, column),
                                'Correction from previous periods التصحيحات من فترة سابقة',
                                lines_format3)
        total_sheet.write('G%s' % (column), '-', lines_format3)
        column += 1
        total_sheet.set_row(column, 30)
        total_sheet.merge_range('B%s:F%s' % (column, column),
                                'Vat credit card forward from previous periods الرصيد الدائن لضريبة القيمة المضافة من فترات سابقى',
                                lines_format3)
        total_sheet.write('G%s' % (column), '-', lines_format3)
        column += 1
        total_sheet.merge_range('B%s:F%s' % (column, column),
                                'Net Vat Due صافي ضريبة القيمة المضافة',
                                total_format3)
        total_sheet.write('G%s' % (column),
                          (sale_total_tax - sale_total_adjustment) - (purchase_total_tax - purchase_total_adjustment),
                          total_format3)
        total_sheet.set_row(column, 30)
        total_sheet.merge_range('A%s:A%s' % (startf_value, column), 'Vat Payment Summary', vat_format3)
