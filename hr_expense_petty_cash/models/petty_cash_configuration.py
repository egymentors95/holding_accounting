# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PettyCashConfiguration(models.Model):
    _name = "petty.cash.configuration"
    _description = "Petty Cash Configuration"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)

    account_id = fields.Many2one(
        comodel_name="account.account",tracking=True, string="Petty Cash Account", required=True, )
    petty_cash_limit = fields.Float(
        string="Max Limit", required=True,tracking=True )
    journal_id = fields.Many2one(
        comodel_name="account.journal",tracking=True )

    type = fields.Selection(
        selection=[('continuous', 'Continuous'), ('temporary', 'Temporary')],
        required=True, tracking=True)
    percent_to_reconcile = fields.Float('Percent To Reconcile')
    expense_limit = fields.Integer('Expense Limit',tracking=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company,tracking=True)
