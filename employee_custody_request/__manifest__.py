# -*- coding: utf-8 -*-
{
    'name': "Custody Management in Odoo: From Request to Settlement",

    'summary': """
Odoo Custody Lifecycle: Request, Disburse, and Settl""",

    'description': """

This course provides a comprehensive, hands-on guide to managing employee custodies (Petty Cash) in Odoo. You'll learn how to handle custody requests (temporary and permanent), disbursement processes, and final settlement using Odoo’s standard expense module. The course focuses on both configuration and operational workflows to ensure smooth and efficient custody management.
    """,

    'author': "ODEX",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','account','exp_payroll_custom','hr_expense','odex25_account_reports','system_dashboard_classic','exp_budget_check'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/report.xml',
        'data/sequence.xml',
        'views/account_journal.xml',
        'views/types_custody.xml',
        'wizard/account_paymrnt_register_views.xml',
        'views/hr_expenes.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
