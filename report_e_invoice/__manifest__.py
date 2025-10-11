# Copyright 2021 Khabir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Report E Invoice',
    'description': """
        E-Invoice Report""",
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Odex25-Accounting/Odex25-Accounting',

    'author': 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    'depends': ['account','sale','purchase'],
    'data': [
        'views/res_partner.xml',
        'report/assets.xml',
        'wizard/account_move_reversal.xml',
        'report/e_invoice.xml',
        'report/e_invoice_without_header.xml',
    ],
    'demo': [
    ],
}
