# -*- encoding: utf-8 -*-
{
    'name': 'Expert - Saudi Arabia - Invoice',
    'version': '1.0.0',
    'icon': '/exp_l10n_sa/static/description/icon.png',
    'category': 'E-invoicing Zatca / Accounting',
    'description': """
    Invoices for the Kingdom of Saudi Arabia
""",
    'depends': ['exp_l10n_sa', 'l10n_gcc_invoice'],
    'data': [
        'views/view_move_form.xml',
        'views/report_invoice.xml',
    ],
    "author": "Expert Company - Abuzar",
    "website": "https://exp-sa.com",
    'license': 'GPL-3',
}
