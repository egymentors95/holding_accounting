# -*- coding: utf-8 -*-
{
    'name': "Budget Hierarchical Report",

    'description': """
        adding hierarchical dynamic report for budget lines and 
        analytic accounts
    """,

    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': [
        'account_budget_custom'
    ],

    'data': [
        'views/client_action_budget.xml',
        'views/views.xml',
    ],
    'qweb': ["static/src/xml/report_template.xml"],

}