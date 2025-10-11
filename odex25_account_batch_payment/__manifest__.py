# -*- coding: utf-8 -*-
{
    'name': 'Batch Payment',
    'version': '1.0',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'description': """
Batch Payments
=======================================
Batch payments allow grouping payments.

They are for example used to regroup serveral received checks before you deposit them in a single batch to the bank.
The total amount deposited will then appear as a single transaction on your bank statement.
When you proceed with the reconciliation, simply select the corresponding batch payment to reconcile all the payments within.
    """,
    'website': 'https://www.odoo.com/page/accounting',
    'depends' : ['odex25_account_accountant'],
    'data': [
        'security/odex25_account_batch_payment_security.xml',
        'security/ir.model.access.csv',
        'data/odex25_account_batch_payment_data.xml',
        'report/odex25_account_batch_payment_reports.xml',
        'report/odex25_account_batch_payment_report_templates.xml',
        'views/odex25_account_batch_payment_templates.xml',
        'views/odex25_account_batch_payment_views.xml',
        'views/account_payment_views.xml',
        'views/account_journal_views.xml',
        'wizard/download_wizard_views.xml',
        'wizard/batch_error_views.xml',
    ],
    'qweb': [
        "static/src/xml/account_reconciliation.xml",
    ],
    'test': [],
    'installable': True,
}
