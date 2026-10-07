import logging

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.session import Session

_logger = logging.getLogger(__name__)


class LogoutWhatsAppSession(Session):
    # Intercept explicit Odoo logout endpoints in Odoo 19.

    def _notify_logout(self):
        try:
            uid = request.session.uid
            db = request.session.db
            if not uid or not db:
                return

            user = request.env["res.users"].sudo().browse(uid).exists()
            if not user:
                return

            # ip = request.httprequest.remote_addr or ""

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

            user.with_context(logout_ip=ip)._send_logout_whatsapp_notification()
        except Exception:
            # Never prevent a user from logging out because WhatsApp failed.
            _logger.exception("Failed to send Odoo logout WhatsApp notification")

    @http.route(
        "/web/session/logout",
        type="http",
        auth="none",
        readonly=True,
    )
    def logout(self, redirect="/odoo"):
        self._notify_logout()
        request.session.logout(keep_db=True)
        return request.redirect(redirect, 303)

    @http.route(
        "/web/session/destroy",
        type="jsonrpc",
        auth="user",
        readonly=True,
    )
    def destroy(self):
        self._notify_logout()
        request.session.logout()
