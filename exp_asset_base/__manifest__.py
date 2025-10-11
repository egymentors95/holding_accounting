# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Asset Extend',
    'summary': 'Adding new features to asset',
    'description': '''
Adding the following Features:
==============================

Alter asset Form

Alter Asset category Form

Alter Product Form

Add asset operations (Transfer, Sell/Dispose, Maitenenace, Assesment)
    ''',
    'version': '1.0.0',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'odex25_account_asset',
        'hr', 'barcodes', 'report_xlsx'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/asset_data.xml',
        'data/asset_cron.xml',
        'reports/reports.xml',
        'reports/asset_barcode_pdf_report.xml',
        'reports/asset_barcode_zpl_report.xml',
        'views/account_asset_view.xml',
        'views/account_asset_adjustment_view.xml',
        'views/menus.xml',
        # 'views/asset_modify_views.xml',
        # 'views/asset_pause_views.xml',
        # 'views/asset_sell_views.xml',
    ],
}
