# -*- coding: utf-8 -*-


{
    'name': 'Import OFX Bank Statement',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'version': '1.0',
    'depends': ['odex25_account_bank_statement_import'],
    'description': """
Module to import OFX bank statements.
======================================

This module allows you to import the machine readable OFX Files in Odoo: they are parsed and stored in human readable format in
Accounting \ Bank and Cash \ Bank Statements.

Bank Statements may be generated containing a subset of the OFX information (only those transaction lines that are required for the
creation of the Financial Accounting records).
    """,
    'data': [
        'wizard/odex25_account_bank_statement_import_views.xml',
    ],
    'installable': True,
    'auto_install': True,

}
