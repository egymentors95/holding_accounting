# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # technical field used to reconcile the journal items in Odoo as they were in Winbooks
    winbooks_matching_number = fields.Char(help="Matching number that was used in Winbooks")
