# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_odex25_account_accountant = fields.Boolean(string='Accounting')
    module_odex25_account_budget = fields.Boolean(string='Budget Management')
    module_odex25_account_reports = fields.Boolean("Dynamic Reports")
    module_odex25_account_batch_payment = fields.Boolean(string='Use batch payments',
                                                         help='This allows you grouping payments into a single batch and eases the reconciliation process.\n'
                                                              '-This installs the account_batch_payment module.')
    module_odex25_account_bank_statement_import_qif = fields.Boolean("Import .qif files")
    module_odex25_account_bank_statement_import_ofx = fields.Boolean("Import in .ofx format")
    module_odex25_account_bank_statement_import_csv = fields.Boolean("Import in .csv format")
    module_odex25_account_bank_statement_import_camt = fields.Boolean("Import in CAMT.053 format")
    module_odex25_account_invoice_extract = fields.Boolean(string="Bill Digitalization")
    module_exp_budget_check = fields.Boolean(string='Vendor Bill Budget')
    module_odex25_account_3way_match = fields.Boolean(string="3-way matching: purchases, receptions and bills")

    @api.onchange('module_odex25_account_budget')
    def onchange_module_account_budget(self):
        if self.module_account_budget:
            self.group_analytic_accounting = True
