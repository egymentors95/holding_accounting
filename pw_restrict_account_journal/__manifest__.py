# -*- coding: utf-8 -*-
{
    "name": "Journal Restriction on Users",
    "version": "1.0",
    'summary': """
        This module is allow you to restrict account journal to the specific users to access allowed journals only | Journal Restriction for users | Journal restricted users | Journal restriction by user | User journal restriction""",
    'description': """
This module is allow you to restrict account journal to the specific users to access allowed journals only
        """,    
    "category": "Accounting",
    'author': "Preway IT Solutions",
    "sequence": 2,
    "depends" : ['account'],
    "data" : [
        'security/account_security.xml',
        'views/res_user_view.xml',
    ],
    'price': 10.0,
    'currency': 'EUR',
    "installable": True,
    "auto_install": False,
    'live_test_url': 'https://youtu.be/xmJqnPFyy30',
    "images":["static/description/Banner.png"],
}
