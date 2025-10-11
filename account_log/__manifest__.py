# -*- coding: utf-8 -*-
{
    'name': "Account Log",

    'summary': """
        Add chatter to accounts, taxes, journals, payment methods, bank accounts & currencies """,

    'description': """
    """,

    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/account_chatter_view.xml',
    ]
}
