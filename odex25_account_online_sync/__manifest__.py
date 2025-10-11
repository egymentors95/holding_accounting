# -*- coding: utf-8 -*-
{
    'name': "odex25_account_online_sync",
    'summary': """
        This module is used for Online bank synchronization.""",

    'description': """
        This module is used for Online bank synchronization. It provides basic methods to synchronize bank statement.
    """,
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'version': '2.0',
    'depends': ['account'],

    'data': [
        'security/ir.model.access.csv',
        'security/odex25_account_online_sync_security.xml',
        'views/online_sync_views.xml',
    ],
    'qweb': [
        'views/online_sync_templates.xml',
    ],
    'auto_install': True,
}
