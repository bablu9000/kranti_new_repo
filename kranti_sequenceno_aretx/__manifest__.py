# -*- coding: utf-8 -*-
{
    'name': 'Sequence No in invoice',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Adds Sr. No column in Invoice PDF',
    'depends': ['base','sale','purchase','account'],
    'data': [
        'views/invoice_report_inherit.xml',
        'views/sale_order_line.xml',
        'views/rfq_print.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
