# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    extract_show_ocr_option_selection = fields.Selection([
        ('no_send', 'Do not digitalize bills'),
        ('manual_send', "Digitalize bills on demand only"),
        ('auto_send', 'Digitalize all bills automatically')], string="Send mode on invoices attachments",
        required=False, default='auto_send')
    extract_single_line_per_tax = fields.Boolean(string="OCR Single Invoice Line Per Tax", default=True)
