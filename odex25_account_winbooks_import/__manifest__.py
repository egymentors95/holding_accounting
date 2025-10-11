# -*- coding: utf-8 -*-

{
    'name': "Account Winbooks Import",
    'summary': """Import Data From Winbooks""",
    'description': """
        Import Data From Winbooks
    """,
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['odex25_account_accountant', 'base_vat'],
    'external_dependencies': {'python': ['dbfread']},
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_wizard_views.xml',
        'views/account_onboarding_templates.xml',
    ],
}
