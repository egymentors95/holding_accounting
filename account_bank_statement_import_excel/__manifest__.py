{
    'name': 'Import Excel Bank Statement',
    'license': 'AGPL-3',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'version': '0.1',
    'depends': [
        'odex25_account_bank_statement_import',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_account_bank_statement_import.xml',
        'views/excel_dimensions_views.xml',
        'data/excel.dimensions.csv'
    ],
    'external_dependencies': {
        'python': ['xlrd'],
    },
    'installable': True,
}
