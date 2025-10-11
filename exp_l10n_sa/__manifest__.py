# -*- encoding: utf-8 -*-
{
    'name': 'Expert - Saudi Arabia - Accounting',
    'version': '2.0',
    'icon': '/exp_l10n_sa/static/description/icon.png',
    'category': 'E-invoicing Zatca / Accounting',
    'description': """
Odoo Arabic localization for most arabic countries and Saudi Arabia.

This initially includes chart of accounts of USA translated to Arabic.

In future this module will include some payroll rules for ME .
""",
    'depends': ['account', 'l10n_multilang'],
    'data': [
        'data/account_data.xml',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/account_tax_group.xml',
        # 'data/demo_company.xml',
        'data/l10n_sa_chart_data.xml',
        'data/account_tax_report_data.xml',
        'data/account_tax_template_data.xml',
        'data/account_fiscal_position_template_data.xml',
        'data/account_chart_template_configure_data.xml',
    ],
    'demo': [
        'demo/demo_company.xml',
    ],
    'post_init_hook': 'load_translations',
    "author": "Expert Company - Abuzar",
    "website": "https://exp-sa.com",
    'license': 'GPL-3',
}
