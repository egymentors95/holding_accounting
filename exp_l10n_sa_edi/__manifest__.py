# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Expert - Saudi Arabia - E-invoicing',
    'icon': '/exp_l10n_sa/static/description/icon.png',
    'version': '0.1',
    'depends': [
        'exp_account_edi_ubl_cii',
        # 'exp_account_debit_note',
        'exp_l10n_sa_invoice',
        'exp_base_vat',
        'exp_l10n_sa'
    ],
    'summary': """
        E-Invoicing, Universal Business Language
    """,
    'description': """
        E-invoice implementation for the Kingdom of Saudi Arabia
    """,
    'category': 'E-invoicing Zatca / Accounting',
    'data': [
        'security/ir.model.access.csv',
        'data/account_edi_format.xml',
        'data/ubl_21_zatca.xml',
        'data/res_country_data.xml',
        'wizard/l10n_sa_edi_otp_wizard.xml',
        'views/account_tax_views.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_view.xml',
        # 'data/demo_company.xml',
        # 'views/report_invoice.xml',
        'templates.xml',
    ],
    'demo': [
        'demo/demo_company.xml',
    ],
    "author": "Expert Company - Abuzar",
    "website": "https://exp-sa.com",
    'license': 'GPL-3',
    # 'assets': {
    #     'web.assets_backend': [
    #         'exp_l10n_sa_edi/static/src/scss/form_view.scss',
    #     ]
    # }
}
