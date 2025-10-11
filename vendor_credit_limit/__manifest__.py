# -*- coding: utf-8 -*-
{
    'name': "Vendor Credit Limit",


    'description': """
       Create Limit for Vendors 
    """,

    'author': "Eslam Mohamed",
    'category': 'Accounting',
    'version': '14.0.0.1',

    'depends': ['base', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/res_partner_views.xml',
    ],

    'installable': True,
    'auto_install': False,
}
