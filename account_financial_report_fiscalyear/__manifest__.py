# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2021 (<http://www.exp-sa.com/>).
#
##############################################################################

{
    'name': 'Account Financial Report Fiscal years',
    'summary': """
        Add Fiscal years field to the Odoo OE standard addons
        financial reports wizard.
    """,
    'version': '14.0.',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'website': 'https://github.com/OCA/account-financial-reporting',
    'author': "Expert Co. Ltd.",
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': True,
    'depends': [
        'account_fiscal_year','account_financial_report'
    ],
    'data': [
        'wizards/accounting_report.xml',
    ],
}
