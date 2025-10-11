# -*- coding: utf-8 -*-

from odoo import fields, models


class ExcelDimensions(models.Model):
    _name = 'excel.dimensions'
    _description = 'The Dimensions of the excel file used in bank statement import'

    name = fields.Char(string='Name')

    company_id = fields.Many2one(comodel_name='res.company', string='Company')

    details_only = fields.Boolean()

    account_number_row = fields.Integer(string='Account Number Row')
    account_number_col = fields.Integer(string='Account Number Column')

    currency_row = fields.Integer(string='Currency Row')
    currency_col = fields.Integer(string='Currency Column')

    balance_start_row = fields.Integer(string='Starting Balance Row')
    balance_start_col = fields.Integer(string='Starting BalanceColumn')

    balance_end_row = fields.Integer(string='Ending Balance Row')
    balance_end_col = fields.Integer(string='Ending Balance Column')

    date_period_row = fields.Integer(string='Date Period Row')
    date_period_col = fields.Integer(string='Date Period Column')

    details_row = fields.Integer(string='Details Row')

    debit_col = fields.Integer(string='Debit Column')

    credit_col = fields.Integer(string='Credit Column')

    balance_col = fields.Integer(string='Balance Column')

    type_col = fields.Integer(string='Type Column')

    note_col = fields.Integer(string='Note Column')

    date_col = fields.Integer(string='Date Column')
    date_format = fields.Char()

    debit_sign = fields.Boolean('Revert Debit Sign')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    excel_dimension = fields.Many2one('excel.dimensions')

    def _get_bank_statements_available_import_formats(self):
        rslt = super(AccountJournal, self)._get_bank_statements_available_import_formats()
        rslt.append('XLS')
        return rslt