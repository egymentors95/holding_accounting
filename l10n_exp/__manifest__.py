# -*- coding: utf-8 -*-


{
    'name': 'Saudi Arabia - Accounting',
    'version': '1.0',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'description': """
This is the latest Saudi Arabia Odoo localisation necessary to run Odoo accounting for Saudi Arabia with:
=================================================================================================
    - Chart of Accounts""",
    
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Accounting/Localizations/Account Charts',
    'depends': ['l10n_multilang', 'account_chart_of_accounts'],
    #'pre_init_hook': '_check_modules',
    'data': [
        'data/l10n_exp_chart_data.xml',
        'data/account.account.template.csv',
        #'data/account.chart.template.csv',
        'data/account_chart_template_data.xml',
    ],
    'auto_install': ['account_chart_of_accounts'],
}
