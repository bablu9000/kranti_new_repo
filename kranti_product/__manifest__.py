{
    'name': 'Kranti Product Customization',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add size field and custom print label for products',
    'description': '''
        Custom product enhancements for Kranti:
        - Size field on product template
        - Custom Print Label button with size, price, barcode, image
    ''',
    'author': 'Kranti',
    'depends': ['product', 'stock', 'uom', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_paperformat.xml',
        'wizard/product_label_wizard_views.xml',
        'wizard/delivery_label_wizard_views.xml',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/report_views.xml',
        'report/product_label_report_views.xml',
        'report/product_label_template.xml',
        'report/delivery_label_template.xml',
        'report/delivery_label_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
