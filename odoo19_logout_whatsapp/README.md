# Odoo 19 WhatsApp Logout Notification

This module is for Odoo 19 Enterprise and depends on the native `whatsapp`
application.

## What it does

When an authenticated user explicitly logs out through:

- `/web/session/logout`
- `/web/session/destroy`

the module tries to send a WhatsApp notification through Odoo's native
WhatsApp functionality.

The notification includes:

- User
- Logout date/time
- Company
- Database
- IP address

A WhatsApp failure is logged and does not prevent the user from logging out.

## Configuration

Open Settings -> Technical -> System Parameters and set:

`logout_whatsapp_notification.enabled`
    True

`logout_whatsapp_notification.phone`
    Destination phone number with country code, e.g. 919876543210

`logout_whatsapp_notification.template_xmlid`
    XML ID of an approved/synced native `whatsapp.template`.

## Native Odoo WhatsApp setup

The Odoo Enterprise WhatsApp application must already be connected to a
WhatsApp Business Platform account. Create an approved WhatsApp template in
the native WhatsApp application and sync it from Meta.

A suitable template can contain variables such as:

Odoo Logout Notification

User: {{1}}
Logout Time: {{2}}
Company: {{3}}
Database: {{4}}
IP Address: {{5}}

Configure the variables according to your Odoo WhatsApp template.

## Important

This module does not directly call Meta, MSG91, Twilio, or another external
WhatsApp provider. It uses Odoo's installed WhatsApp module.

An explicit logout can be detected. Closing the browser, shutting down a
computer, losing network connectivity, or a browser crash cannot reliably be
treated as a logout because the Odoo server may never receive a logout request.
