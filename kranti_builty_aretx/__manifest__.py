{
    "name": "Kranti Builty WhatsApp",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "author": "Areterix Technologies",
    "summary": "Send Builty through WhatsApp from Invoice",
    "description": """
Kranti Builty WhatsApp
======================

Adds Builty image upload functionality to customer invoices
and provides WhatsApp Builty sending functionality..
""",
    "license": "LGPL-3",
    "depends": [
        "account",
        "whatsapp",
    ],
    "data": [
        "views/account_move_views.xml",
        "report/builty_report.xml",
        "report/builty_report_templates.xml",
    ],
    "installable": True,
    "application": False,
}