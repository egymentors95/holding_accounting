# -*- coding: utf-8 -*-
{
    'name': 'Journal Entry Report',
    'version': '1',
    'summary': 'Journal Entry Report',
    'description': """  """,
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['account'],
    'data': [
        'views/account_move_view.xml',
        'reports/report_journal_entry.xml'
    ],

    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
