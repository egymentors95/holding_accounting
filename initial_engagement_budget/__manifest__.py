# -*- coding: utf-8 -*-
{
    'name': "Initial engagement budget",
    'description': """
        Add new features to budget :
        - Initial engagement budget workflow.
        - Budget Confirmation.
    """,
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25 Accounting/Accounting',
    # any module necessary for this one to work correctly
    'depends': ['account_budget_custom', 'purchase_requisition_custom', 'exp_budget_check'],
    # always loaded
    'data': [
        'security/groups.xml',
        'views/account_budget_views.xml',
        'views/purchase_request_view.xml',
        'views/res_config_view.xml',
        'views/account_payment_view.xml',
        'views/account_move_view.xml',
    ],
}
