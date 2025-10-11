# -*- coding: utf-8 -*-

{
    'name': 'Budget Management',
    'category': 'Odex25 Accounting/Accounting',
    'description': """
Use budgets to compare actual with expected revenues and costs
--------------------------------------------------------------
""",
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['account_configuration'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'wizard/crossovered_budget_percentage_wizard_views.xml',
        'views/account_budget_views.xml',
        'views/account_analytic_account_views.xml',
    ],
    'demo': ['data/account_budget_demo.xml'],
}
