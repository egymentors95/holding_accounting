# -*- coding: utf-8 -*-
{
    "name": "Tax Report Detailed",
    "version": "11.0.1.0.0",
    "summary": "Tax report with fiscal positions",
    'license': 'AGPL-3',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    "depends": [
        'account',
        'report_xlsx',
        'account_fiscal_year'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/tax_report_details_view.xml',
        'views/report.xml',
        'views/account_tax_views.xml',
        'wizard/tax_report_wiz_view.xml',
    ],
    'installable': True,
}
