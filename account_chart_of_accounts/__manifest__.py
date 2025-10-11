# -*- coding: utf-8 -*-
{
    'name': "Hierarchy Chart Of Accounts",

    'summary': """
        Hierarchy Chart Of Accounts""",

    'description': """
        Add Hierarchy Chart Of Accounts
        to odoo because the chart of accounts in standard odoo
        is flat .
        so we add Hierarchy to odoo using parent
    """,

    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'odex25_account_reports','mail'],

    # always loaded
    'data': [
        'data/data_account_type.xml',
        # 'data/account.account.csv',
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_account_view.xml',
        'views/res_config_settings_views.xml',
        'reports/account_report_coa.xml',
    ],

    # 'qweb': ["static/src/xml/hierarchical_chart_templates.xml"],

}
