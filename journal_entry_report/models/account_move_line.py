# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move.line"

    einvoice = fields.Char(string="E-invoice", copy=False)
