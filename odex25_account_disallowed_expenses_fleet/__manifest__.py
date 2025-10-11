# -*- coding: utf-8 -*-
{
    'name': 'Disallowed Expenses on Fleets',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': 'Manage disallowed expenses with fleets',
    'description': "",
    'version': '1.0',
    'depends': ['account_fleet', 'odex25_account_disallowed_expenses'],
    'data': [
        'security/ir.model.access.csv',
        'views/odex25_account_disallowed_expenses_category_views.xml',
        'views/fleet_vehicle_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
