# -*- coding: utf-8 -*-

{
    'name': 'Account Automatic Transfers',
    'depends': ['odex25_account_accountant'],
    'description': """
Account Automatic Transfers
===========================
Manage automatic transfers between your accounts.
    """,
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/transfer_model_views.xml',
    ],
    'application': False,
    'auto_install': True
}
