# -*- coding: utf-8 -*-
{
    'name': "Odoo Tally Integration",

    'summary': """
        Connect and integrate Odoo with Tally accounting software.""",

    'description': """
        Provides seamless integration between Odoo and Tally, allowing for the synchronization of data such as:
        - Chart of Accounts
        - Customers and Suppliers
        - Sales and Purchase Orders
        - Invoices and Bills
        - Payments
        ... and more.

        This module aims to streamline accounting processes and reduce manual data entry.
    """,

    'author': "Mohammad Husen",
    'website': "Your Website/Company Website (Optional)",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.0',  # Consider a more semantic versioning (e.g., 1.0.0)

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account'],  # Added 'account' as it's likely needed for accounting integration

    # always loaded
    'data': [
        'security/ir.model.access.csv',  # Ensure you have proper access rights defined
        # 'views/views.xml',  # Your main views for the module
        'views/menu_setting_view.xml',  # Keep this if it's relevant
        # 'views/templates.xml', # If you have any website templates
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],

    "application": True,
    "installable": True,
    "auto_install": False,  # Consider making this False initially for better control

    'external_dependencies': {
        'python': ['pypeg2']  # Keep this if your integration relies on it
    },

    'license': 'LGPL-3',  # Specify the license
}