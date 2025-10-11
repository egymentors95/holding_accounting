# -*- coding: utf-8 -*-

{
    'name': "Odex25 Analytic Accounting",
    'version': '0.1',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['analytic', 'account'],
    'description': """
Module for defining analytic accounting object.
===============================================

In Odoo, analytic accounts are linked to general accounts but are treated
totally independently. So, you can enter various different analytic operations
that have no counterpart in the general financial accounts.
    """,
    'data': [
        'views/account_analytic_view.xml'
    ],
    'installable': True,
    'auto_install': True,
}
