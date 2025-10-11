# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2022 (<http://www.exp-sa.com/>).
#
##############################################################################

{
    "name" : "Postdated Cheque Management(PDC) Odoo",
    "author": "Expert Co. Ltd.",
    "version" : "14.0",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'summary': 'Apply PDC Payment, Generate Payment and Journal Entries With PDC Account.',
    "description": """ Apply PDC Payment, Generate Payment and Journal Entries With PDC Account.""", 
    "depends" : ['account_check_printing'],
    "data": [
        'data/account_payment_method_data.xml',
        'views/account_payment_view.xml',
        'wizard/account_payment_register_views.xml',
    ],
    "auto_install": False,
    "installable": True,
}

