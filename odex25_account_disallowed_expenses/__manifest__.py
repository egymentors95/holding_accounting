# -*- coding: utf-8 -*-
{
    'name': 'Disallowed Expenses',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': 'Manage disallowed expenses',
    'description': 'Manage disallowed expenses',
    'version': '1.0',
    'depends': ['odex25_account_reports'],
    'data': [
        'report/odex25_account_disallowed_expenses_report_views.xml',
        'security/ir.model.access.csv',
        'security/odex25_account_disallowed_expenses_security.xml',
        'views/account_account_views.xml',
        'views/odex25_account_disallowed_expenses_category_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
