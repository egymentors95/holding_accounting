# -*- coding: utf-8 -*-
################################################################################
{
    'name': "Account Attachments",
    'version': '14.0.1.0.0',
    'category': 'Account',
    'summary': 'Helps to view all documents attached to account',
    'description': """account Attachments module allows user to view 
        all the documents attached to account.""",
    'company': 'Expert',
    'website': 'https://www.expert.com',
    'depends': ['base','account'],
    'data': [
        'views/account_move_view.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
