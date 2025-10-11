# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_petty_paid = fields.Boolean(string='Paid by Petty Cash', default=False)
    petty_employee_id = fields.Many2one('hr.employee', string='Petty Cashier', copy=False)