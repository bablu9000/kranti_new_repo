{
    'name': 'Kranti Discount Price in Invoice Pdf',
    'author': 'Areterix Technologies',
    'license': 'LGPL-3',
    'version': '19.0.0.1',
    'application': False,
    'installable': True,
    'depends': ['account', 'sale'],
    'data': [
        
        'views/report_invoice.xml',
        'views/report_rfq.xml',
        'views/sale_order_line.xml',
        'views/account_move_line.xml',
        
    ],
}