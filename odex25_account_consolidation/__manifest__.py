# -*- coding: utf-8 -*-
{
    'name': "Consolidation",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'sequence': 205,
    'summary': """All you need to make financial consolidation""",
    'description': """All you need to make financial consolidation""",
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['odex25_account_reports','odex25_web_grid'],
    'data': [
        'security/odex25_account_consolidation_security.xml',
        'security/ir.model.access.csv',
        'report/trial_balance.xml',
        'views/assets.xml',
        'views/account_account_views.xml',
        'views/account_move_views.xml',
        'views/consolidation_account_views.xml',
        'views/consolidation_journal_views.xml',
        'views/consolidation_period_views.xml',
        'views/consolidation_account_group_views.xml',
        'views/consolidation_chart_views.xml',
        'views/consolidation_rate_views.xml',
        'views/menuitems.xml',
        'views/onboarding_templates.xml',
    ],
    'qweb': [
        'static/src/xml/fields_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
