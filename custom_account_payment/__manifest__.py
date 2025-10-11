{
    'name': 'Automatic Payment Pairing',
    'version': '1.0',
    'website': 'http://exp-sa.com',
    'license': 'GPL-3',
    'author': 'Expert Co. Ltd.',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'summary': 'Automatically create paired payment for internal transfers in Payment.'
    ,
    'description': """
        This module enhances the Odoo Payment system by introducing automatic payment pairing for internal transfers. 
        When a payment is posted, a corresponding paired payment is automatically generated in the specified destination journal.
        The two payments are cross-referenced, providing a seamless link between them.
    """,
    'depends': ['base', 'account'],
    'data': [
        'views/account_payment.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
