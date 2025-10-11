{
    'name': 'Customer Balance in Invoice',
    'version': '14.0.1.0.0',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'summery': 'Check for customer credit on Invoice View/Print',
    'author': 'INKERP',
    'website': "https://www.INKERP.com",
    'depends': ['account'],
    
    'data': [
        'reports/account_report_template.xml',
        'views/account_move_view.xml',
    ],
    
    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
