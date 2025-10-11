# -*- coding: utf-8 -*-
{
    'name': "Custom Budget",
    'description': """
        Add new features to budget :
        - Budget Increase/Decrease & Transfer operation.
        - Budget Confirmation.
    """,
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25 Accounting/Accounting',
    # any module necessary for this one to work correctly
    'depends': ['odex25_account_budget', 'odex25_account_reports', 'report_xlsx'],
    # always loaded
    'data': [
        'data/budget_operation_data.xml',
        'security/budget_groups.xml',
        'security/ir.model.access.csv',
        'views/account_budget_views.xml',
        'views/budget_operations_view.xml',
        'views/budget_confirmation_view.xml',
        'views/menus.xml',
        'reports/reports.xml'
    ],
}
