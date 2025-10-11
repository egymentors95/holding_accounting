# -*- coding: utf-8 -*-
{
    'name': 'Odex25 Accounting',
    'version': '1.1',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'sequence': 30,
    'summary': 'Manage financial and analytic accounting',
    'description': """
Accounting Access Rights
========================
It gives the Administrator user access to all accounting features such as journal items and the chart of accounts.

It assigns manager and user access rights to the Administrator for the accounting application and only user rights to the Demo user.
""",
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['account', 'web_tour'],
    'data': [
        'data/odex25_account_accountant_data.xml',
        'data/digest_data.xml',
        'security/ir.model.access.csv',
        'security/odex25_account_accountant_security.xml',
        'views/odex25_account_accountant_templates.xml',
        'views/account_account_views.xml',
        'views/account_bank_statement_views.xml',
        'views/account_fiscal_year_view.xml',
        'views/account_journal_dashboard_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/odex25_account_accountant_menuitems.xml',
        'views/digest_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'wizard/account_change_lock_date.xml',
        'wizard/reconcile_model_wizard.xml',
    ],
    'qweb': [
        "static/src/xml/account_reconciliation.xml",
    ],
    'demo': ['data/odex25_account_accountant_demo.xml'],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': '_odex25_account_accountant_post_init',
    'uninstall_hook': "uninstall_hook",
}
