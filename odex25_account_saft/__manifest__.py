# -*- coding: utf-8 -*-

{
    'name': 'Standard Audit File for Tax Base module',
    'version': '1.0',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'description': """
Base module for SAF-T reporting
===============================
This is meant to be used with localization specific modules.
    """,
    'depends': [
        'odex25_account_reports'
    ],
    'data': [
        'views/saft_templates.xml',
    ],
}
