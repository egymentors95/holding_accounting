# -*- coding: utf-8 -*-
{
    "name": "Odoo Dynamic Bank Cheque Print",
    "summary": """The module allows you to add various fields to the cheque template in Odoo, so you can print the cheque from Odoo.""",

    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    'license': 'AGPL-3',
    "description": """Odoo Dynamic Bank Cheque Print
Print cheque from bank in Odoo
Print bank check in Odoo
bank check print
Odoo Bank cheque printing
Print payment check
Digital Check writing in Odoo
Odoo Partner cheque print""",
    "depends": [
        'account',
        'website',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/cheque_attribute_data.xml',
        'wizard/print_cheque_transient_views.xml',
        'views/account_payment_view.xml',
        'views/bank_cheque_views.xml',
        'views/website_template_view.xml',
        'views/cheque_report.xml',
    ],
    "images": ['static/description/Banner.png'],
    "application": True,
    "installable": True,
    "auto_install": False,
}
