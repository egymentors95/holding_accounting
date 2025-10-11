# -*- coding: utf-8 -*-

{
    'name': 'Payment Follow-up Management',
    'version': '1.0',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'description': """
Module to automate letters for unpaid invoices, with multi-level recalls.
=========================================================================

You can define your multiple levels of recall through the menu:
---------------------------------------------------------------
    Configuration / Follow-up / Follow-up Levels

Once it is defined, you can automatically print recalls every day through simply clicking on the menu:
------------------------------------------------------------------------------------------------------
    Payment Follow-Up / Send Email and letters

It will generate a PDF / send emails / set manual actions according to the different levels
of recall defined. You can define different policies for different companies.

""",
    'depends': ['account', 'mail', 'sms', 'odex25_account_reports'],
    'data': [
        'security/odex25_account_followup_security.xml',
        'security/ir.model.access.csv',
        'security/sms_security.xml',
        'data/odex25_account_followup_data.xml',
        'data/cron.xml',
        'views/odex25_account_followup_views.xml',
        'views/partner_view.xml',
        'views/report_followup.xml',
        'views/account_journal_dashboard_view.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/odex25_account_followup_template.xml',
    ],
    'demo': [
        'demo/odex25_account_followup_demo.xml'
    ],
    'installable': True,
    'auto_install': True,
}
