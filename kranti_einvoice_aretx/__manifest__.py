{
    'name': "Kranti E-Invoice",
    'version': '19.0.0.1',
    'author': 'Areterix Technologies',
    'license': 'LGPL-3',
    'depends': [
        'base', 'whatsapp', 'contacts', 'account', 'l10n_in_edi', 'stock', 'product', 'sale', 'sale_stock',
        'account_reports','l10n_in','l10n_in_ewaybill'
    ],
    'assets': {
        'web.report_assets_common': [
            'kranti_einvoice_aretx/static/src/css/custom_ewaybill.css',
            'kranti_einvoice_aretx/static/src/css/custom_einvoice_layout.scss',

        ],
        'web.assets_backend': [
            'kranti_einvoice_aretx/static/src/css/wizard.scss',
            'kranti_einvoice_aretx/static/src/xml/whatsapp.xml',
            'kranti_einvoice_aretx/static/src/css/hide_chatter_whatsapp.css',
            'kranti_einvoice_aretx/static/src/js/package_button.js',
            'kranti_einvoice_aretx/static/src/xml/package_button.xml',

        ],
    },

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_partner_views.xml',
        'views/l10_in_ewaybill.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'reports/custom_ewaybill_report_template.xml',
        'reports/custom_ewaybill_report.xml',
        'reports/custom_einvoice_layout.xml',
        'reports/custom_einvoice_report_template.xml',
        'reports/custom_einvoice_report.xml',
        'wizard/package_selection_wizard_view.xml',
        'button/package_button_in_so.xml',
        'stock_picking/hide_partner_id.xml',
        'stock_picking/delivery_slip.xml',
        'reports/report_picking_hide.xml',
        'reports/sale_order_report_inherit.xml',

    ],
    'application': False,
    'installable': True
}
