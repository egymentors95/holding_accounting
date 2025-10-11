# -*- coding: utf-8 -*-


{
    'name': 'Assets Management',
    'description': """
Assets management
=================
Manage assets owned by a company or a person.
Keeps track of depreciations, and creates corresponding journal entries.

    """,
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    'sequence': 32,
    'depends': ['odex25_account_reports','mrp' ],
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/asset_modify_views.xml',
        'wizard/asset_pause_views.xml',
        'wizard/asset_sell_views.xml',
        'views/account_account_views.xml',
        'views/account_asset_views.xml',
        'views/account_deferred_revenue.xml',
        'views/account_deferred_expense.xml',
        'views/account_move_views.xml',
        'views/account_asset_templates.xml',
        'views/mrp_views.xml',
        'views/product_category_views.xml',
        'report/account_assets_report_views.xml',
    ],
    'demo': [
        'demo/account_deferred_revenue_demo.xml',
    ],
    'qweb': [
        "static/src/xml/account_asset_template.xml",
    ],
    # 'auto_install': True,
}
