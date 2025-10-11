# -*- coding: utf-8 -*-
{
    'name' : 'Cash Basis Accounting Reports',
    'summary': 'Add cash basis functionality for reports',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'description': """
Cash Basis for Accounting Reports
=================================
    """,
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['odex25_account_reports'],
    'data': [
        'data/account_financial_report_data.xml',
        'views/account_report_view.xml',
        'views/report_financial.xml',
    ],
    'installable': True,
}
