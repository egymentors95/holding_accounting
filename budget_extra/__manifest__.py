# -*- coding: utf-8 -*-
{
    'name': 'Budget Extra Fields',
    'version': '1.1',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'sequence': 30,
    'summary': 'Manage Budget Classifications and Programs',
    'description': """ Fix issues with payment
""",
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['account_budget_custom','hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
