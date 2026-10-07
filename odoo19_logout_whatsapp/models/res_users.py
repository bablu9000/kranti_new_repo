import inspect
import logging
from odoo.http import request
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _send_logout_whatsapp_notification(self):
        self.ensure_one()

        icp = self.env["ir.config_parameter"].sudo()
        enabled = icp.get_param(
            "logout_whatsapp_notification.enabled", "True"
        ).lower() in ("1", "true", "yes", "on")
        if not enabled:
            return False

        phone = icp.get_param(
            "logout_whatsapp_notification.phone", ""
        ).strip()
        template_xmlid = icp.get_param(
            "logout_whatsapp_notification.template_xmlid",
            "",
        ).strip()

        if not phone:
            _logger.warning(
                "Logout WhatsApp notification skipped: destination phone "
                "is not configured."
            )
            return False

        # if not template_xmlid:
        #     _logger.warning(
        #         "Logout WhatsApp notification skipped: "
        #         "logout_whatsapp_notification.template_xmlid is empty."
        #     )
        #     return False
        # template = self.env.ref(template_xmlid, raise_if_not_found=False)
        template = request.env[
                'whatsapp.template'
            ].sudo().search([
                ('name', '=', 'Odoo Logout Alert'),
            ], limit=1)
            # ('status', '=', 'approved'),

        if not template:
            _logger.warning(
                "Logout template not found."
            )
            return False

        now = fields.Datetime.now()
        # ip = self.env.context.get("logout_ip") or "N/A"
        http_request = request.httprequest
        forwarded_for = http_request.headers.get(
            'X-Forwarded-For'
        )

        real_ip = http_request.headers.get(
            'X-Real-IP'
        )
        ip = False
        if forwarded_for:
            client_ip = (
                forwarded_for
                .split(',')[0]
                .strip()
            )

            if client_ip:
                ip = client_ip
            
        elif real_ip and ip == False:
            ip = real_ip.strip()
        else:
            ip = http_request.remote_addr  

        company = self.company_id.display_name if self.company_id else "N/A"

        body = (
            "Odoo Logout Notification\n\n"
            "User: %s\n"
            "Logout Time: %s\n"
            "Company: %s\n"
            "Database: %s\n"
            "IP Address: %s"
            % (
                self.display_name,
                fields.Datetime.context_timestamp(self, now).strftime(
                    "%d-%b-%Y %H:%M:%S"
                ),
                company,
                self.env.cr.dbname,
                ip,
            )
        )

        notification = self.env["logout.whatsapp.notification"].sudo().create({
            "name": "Logout - %s" % self.display_name,
            "phone": phone,
            "message": body,
            "user_id": self.id,
            "logout_datetime": now,
            "ip_address": ip,
            "company_id": self.company_id.id,
        })

        composer = request.env[
            'whatsapp.composer'
        ].sudo().create({
            'res_ids': str(notification.ids),
            'res_model': 'logout.whatsapp.notification',
            'wa_template_id': template.id,
        })

        composer._send_whatsapp_template(
            force_send_by_cron=True
        )
        user = self.env.user
        _logger.info(
            "Logout WhatsApp Alert sent successfully. "
            "User=%s, IP=%s",
            user.name,
            ip,
        )

        # for method_name in (
        #     "_send_whatsapp_template",
        #     "send_whatsapp_template",
        #     "_send_whatsapp",
        # ):
        #     method = getattr(template, method_name, None)
        #     if not method:
        #         continue

        #     try:
        #         sig = inspect.signature(method)
        #         names = set(sig.parameters)
        #         kwargs = {}

        #         if "res_ids" in names:
        #             kwargs["res_ids"] = [notification.id]
        #         elif "records" in names:
        #             kwargs["records"] = notification
        #         elif "record" in names:
        #             kwargs["record"] = notification
        #         if "phone" in names:
        #             kwargs["phone"] = phone
        #         if "force_send" in names:
        #             kwargs["force_send"] = True
        #         if "whatsapp_account" in names:
        #             account = (
        #                 getattr(template, "wa_account_id", False)
        #                 or getattr(template, "account_id", False)
        #             )
        #             if account:
        #                 kwargs["whatsapp_account"] = account

        #         result = method(**kwargs)
        #         _logger.info(
        #             "Odoo logout WhatsApp notification sent using %s; result=%r",
        #             method_name,
        #             result,
        #         )
        #         return True
        #     except Exception:
        #         _logger.exception(
        #             "Native WhatsApp method %s failed for logout notification",
        #             method_name,
        #         )

        # Fallback for builds exposing the native WhatsApp composer.
        # composer_model = self.env.get("whatsapp.composer")
        # if composer_model:
        #     try:
        #         vals = {
        #             "res_model": notification._name,
        #             "res_ids": str([notification.id]),
        #             "wa_template_id": template.id,
        #         }
        #         composer = composer_model.sudo().create(vals)
        #         action = getattr(composer, "action_send_whatsapp", None)
        #         if action:
        #             action()
        #             _logger.info(
        #                 "Odoo logout WhatsApp notification sent through "
        #                 "whatsapp.composer."
        #             )
        #             return True
        #     except Exception:
        #         _logger.exception("Native WhatsApp composer fallback failed.")

        # _logger.error(
        #     "No supported native Odoo 19 WhatsApp sending entry point was found. "
        #     "Check the installed Enterprise WhatsApp module and template."
        # )
        return False
