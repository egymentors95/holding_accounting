# -*- coding: utf-8 -*-


{
    'name': 'Import CAMT Bank Statement',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['odex25_account_bank_statement_import'],
    'description': """
Module to import CAMT bank statements.
======================================

Improve the import of bank statement feature to support the SEPA recommended Cash Management format (CAMT.053).
    """,
    'data': [
        'data/odex25_account_bank_statement_import_data.xml'
    ],

    'auto_install': True,
}
