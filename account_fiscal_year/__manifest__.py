# Copyright 2016 Camptocamp SA
# Copyright 2018 Lorenzo Battistini <https://github.com/eLBati>
# Copyright 2020 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Fiscal Year",
    "summary": "Create Account Fiscal Year",
    "version": "14.0.1.1.1",
    "development_status": "Production/Stable",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    "website": "https://github.com/OCA/account-financial-tools"
    "14.0/account_fiscal_year",
    "author": "Agile Business Group, Camptocamp SA, "
    "Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "AGPL-3",
    "depends": [
        "account","odex25_account_budget"
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/account_fiscal_year_rule.xml",
        "views/account_fiscal_year_views.xml",
        "views/account_view.xml",
        "views/account_budget_views.xml",
        "wizard/account_opening_view.xml",
    ],
}
