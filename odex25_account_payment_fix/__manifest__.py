# -*- coding: utf-8 -*-
{
    'name': 'Odex25 Payment Fix',
    'version': '1.1',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'sequence': 30,
    'summary': 'Manage financial and analytic accounting',
    'description': """ Fix issues with payment
""",
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['account', 'odex25_account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
