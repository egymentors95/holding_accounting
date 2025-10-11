# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice Extract',
    'version': '1.0',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'summary': 'Extract data from invoice scans to fill them automatically',
    'depends': ['account', 'iap', 'account_configuration'],
    'data': [
        'security/ir.model.access.csv',
        'data/odex25_account_invoice_extract_data.xml',
        'data/config_parameter_endpoint.xml',
        'data/extraction_status.xml',
        'data/res_config_settings_views.xml',
        'data/update_status_cron.xml',
    ],
    'auto_install': True,
    'qweb': [
        'static/src/bugfix/bugfix.xml',
        'static/src/xml/invoice_extract_box.xml',
        'static/src/xml/invoice_extract_button.xml',
    ],
}
