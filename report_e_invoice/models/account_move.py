import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tax_line_amount = fields.Float(compute='_get_tax_amount_line')

    @api.depends('product_id', 'price_unit', 'discount', 'tax_ids')
    def _get_tax_amount_line(self):
        for line in self:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(price_reduce, quantity=line.quantity, product=line.product_id,
                                                 partner=line.move_id.partner_id)['taxes']
                line.tax_line_amount = sum(t.get('amount', 0.0) for t in taxes)
            else:
                line.tax_line_amount = 0


class AccountMove(models.Model):
    _inherit = 'account.move'

    qr_string = fields.Char(compute='_compute_qr_code_str')

    @api.depends('amount_total', 'amount_untaxed', 'invoice_date', 'company_id', 'company_id.vat')
    def _compute_qr_code_str(self):

        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        for record in self:
            qr_code_str = ''
            if record.invoice_date and record.company_id.vat:
                invoice_date = datetime.datetime.strptime(str(record.invoice_date), DEFAULT_SERVER_DATE_FORMAT)
                seller_name_enc = get_qr_encoding(1, record.company_id.name)
                company_vat_enc = get_qr_encoding(2, record.company_id.vat)
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'),
                                                            invoice_date)
                timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
                invoice_total_enc = get_qr_encoding(4, str(record.amount_total))
                total_vat_enc = get_qr_encoding(5, str(record.currency_id.round(
                    record.amount_total - record.amount_untaxed)))

                str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
                qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            record.qr_string = qr_code_str
            record.l10n_sa_qr_code_str = qr_code_str

    @api.depends('line_ids.sale_line_ids')
    def _get_sale_orders(self):
        for move in self:
            if move.move_type == 'out_invoice':
                orders = move.line_ids.sale_line_ids.order_id
                move.sale_ids = orders
            else:
                move.sale_ids = False

    @api.depends('line_ids.purchase_line_id')
    def _get_purchase_orders(self):
        for move in self:
            if move.move_type == 'in_invoice':
                orders = move.line_ids.mapped('purchase_line_id.order_id')
                move.purchase_ids = orders
            else:
                move.purchase_ids = False

    sale_ids = fields.Many2many("sale.order",
                                string='Invoices', compute="_get_sale_orders",
                                readonly=True,
                                copy=False)

    purchase_ids = fields.Many2many("purchase.order",
                                    string='Invoices', compute="_get_purchase_orders",
                                    readonly=True,
                                    copy=False)

    reversal_reason = fields.Char("Reason")
    selection_reason = fields.Selection(
        string='Reason',
        selection=[('edit_stop', 'Edit Or Stop'), ('change_complete_edit', 'Change Or complete Edit'),
                   ('edit_amount', 'Edit Amount'), ('refund_goods', 'Refund Goods')]
    )
    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')
    picking_delivery_date = fields.Date("Picking Delivery Date", compute="_compute_picking_delivery_date")

    def _compute_picking_delivery_date(self):
        for move in self:
            move.picking_delivery_date = False
            if move.move_type == 'out_invoice':
                if len(move.sale_ids) > 0 and len(move.sale_ids[-1].picking_ids) > 0:
                    move.picking_delivery_date = move.sale_ids[-1].picking_ids[-1].scheduled_date
            elif move.move_type == 'in_invoice':
                if len(move.purchase_ids) > 0 and len(move.purchase_ids[-1].picking_ids) > 0:
                    move.picking_delivery_date = move.purchase_ids[-1].picking_ids[-1].scheduled_date

    def _generate_qr_code(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_refund']:
                partner_name = rec.company_id.partner_id.name
            elif rec.move_type in ['in_invoice', 'out_refund']:
                partner_name = rec.partner_id.name
            else:
                partner_name = rec.partner_id.name
            partner_name = str(_('اسم المورد: \t \t ' + str(partner_name) ))
            partner_vat = "##########"
            if rec.move_type in ['out_invoice', 'in_refund']:
                if rec.company_id.partner_id.vat:
                    partner_vat = rec.company_id.partner_id.vat
                    # raise UserError(_('Please define the Company Tax ID'))
            if rec.move_type in ['in_invoice', 'out_refund']:
                if rec.partner_id.vat:
                    partner_vat = rec.partner_id.vat

            partner_vat = str(_('رقم تسجيل ضريبة: \t \t ' + str(partner_vat)))

            currency_total = ''.join([rec.currency_id.name, str(rec.amount_total)])
            total = str(_('إجمالي الفاتورة:  \t \t ' + str(currency_total)))
            currency_tax = ''.join([rec.currency_id.name, str(rec.amount_tax)])
            tax = str(_('إجمالي ضريبة القيمة المضافة:  \t \t ' + str(currency_tax)))
            date_invoice = str(rec.invoice_date)
            date = str(_('الطابع الزمني للفاتورة:  \t \t ' + str(date_invoice)))
            lf = '\n\n'
            ibanqr = lf.join([partner_name, partner_vat, date, total, tax])
            rec.qr_image = generate_qr_code(ibanqr)


def generate_qr_code(value):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_img = base64.b64encode(temp.getvalue())
    return qr_img
