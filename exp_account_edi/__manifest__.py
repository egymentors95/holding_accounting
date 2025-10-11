# -*- coding: utf-8 -*-
{
    'name' : 'Expert - Import/Export Invoices From XML/PDF',
    'description':"""
Electronic Data Interchange
=======================================
EDI is the electronic interchange of business information using a standardized format.

This is the base module for import and export of invoices in various EDI formats, and the
the transmission of said documents to various parties involved in the exchange (other company,
governements, etc.)
    """,
    'version' : '1.0',
    'category': 'E-invoicing Zatca / Accounting',
    'depends' : ['account'],
    "author": "Expert Company - Abuzar",
    "website": "https://exp-sa.com",
    'icon': '/exp_l10n_sa/static/description/icon.png',
    'license': 'GPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/account_edi_document_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/account_journal_views.xml',
        'data/cron.xml'
    ],

}
