# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Petty Cash",
    "version": "13.0.1.1.0",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    "license": "AGPL-3",
    'author': 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    "depends": ["hr_expense", "exp_payroll_custom",'hr'],
    "data": [
        "security/security.xml",
        "data/petty_cash_data.xml",
        "data/hr_expense_data.xml",
        "security/ir.model.access.csv",
        "views/petty_cash_views.xml",
        "views/petty_cash_configuration_views.xml",
        "views/account_move_views.xml",
        "views/hr_expense_sheet_views.xml",
        "views/hr_expense_views.xml",
        'views/menu_security_cus.xml',
        "report/hr_expense_report.xml","wizards/cancel_purchase_request.xml",
    ],
    "installable": True,
}
