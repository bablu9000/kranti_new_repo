# -*- coding: utf-8 -*-
{
    'name': 'User Login Alert',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Secure Odoo account by alerts user about any login 
     happened from any systems""",
    'description': """Secure your Odoo account by alerts at right time. If any
     successful login to user's account happens, an alert mail will be send to 
     user with the browser and IP details.""",
    'author': 'Golu',
    'company': 'Golu',
    'maintainer': 'Golu',
    'depends': ['mail'],
    'data': [
        'security/user_login_alert_groups.xml',
        'views/res_users_views.xml',
    ],
    'external_dependencies': {'python': ['httpagentparser']},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
