# -*- coding: utf-8 -*-
##############################################################################
#
#    (Odex - Extending the base module).
#    Copyright (C) 2017 Expert Co. Ltd. (<http://exp-sa.com>).
#
##############################################################################
{
    'name': 'Odex25 Accounting Base',
    'version': '1.0',
    'author': 'Expert Co. Ltd.',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'description': """
Odex - Extending the accounting module
    """,
    'website': 'http://www.exp-sa.com',
    'depends':
        ['account_log','account_move_line_product','journal_entry_report','odex25_account_accountant','odex25_account_asset','odex25_account_budget','odex25_account_followup','odex25_account_reports','odex25_analytic','tax_report_detailed'],

    'data': [],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
