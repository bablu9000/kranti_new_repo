{
    "name": "Odoo 19 WhatsApp Logout Notification",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Send a WhatsApp notification when an Odoo user explicitly logs out",
    "description": "Uses Odoo Enterprise's native WhatsApp module; no separate WhatsApp API.",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["web", "whatsapp"],
    "data": [
        "data/ir_config_parameter.xml",
    ],
    "installable": True,
    "application": False,
}
