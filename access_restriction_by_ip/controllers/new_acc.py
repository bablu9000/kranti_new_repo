# -*- coding: utf-8 -*-

import odoo
from odoo import fields, models
from datetime import timedelta
from odoo import http
from odoo.addons.web.controllers import home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.http import request
from odoo.tools.translate import LazyTranslate, _
import socket
import logging

_logger = logging.getLogger(__name__)

_lt = LazyTranslate(__name__)


SIGN_UP_REQUEST_PARAMS = {
    'db',
    'login',
    'debug',
    'token',
    'message',
    'error',
    'scope',
    'mode',
    'redirect',
    'redirect_hostname',
    'email',
    'name',
    'partner_id',
    'password',
    'confirm_password',
    'city',
    'country_id',
    'lang',
    'signup_email',
}

CREDENTIAL_PARAMS = ['login', 'password', 'type']


class Home(home.Home):

    def _send_login_whatsapp_alert(
        self,
        user_id,
        login,
        ip_address,
    ):
        """
        Send WhatsApp notification after successful login.
        """
        try:

            # ---------------------------------------------------------
            # Get user
            # ---------------------------------------------------------

            user = request.env['res.users'].sudo().browse(user_id)

            if not user.exists():
                _logger.warning(
                    "Login WhatsApp Alert: user %s does not exist.",
                    user_id,
                )
                return

            # ---------------------------------------------------------
            # WhatsApp recipient
            # ---------------------------------------------------------
            #
            # Change this number to your administrator/security
            # WhatsApp number.
            #
            # Country code required.
            #
            # Example:
            # India +91 9876543210
            # => 919876543210
            #
            # ---------------------------------------------------------

            whatsapp_number = (
                request.env['ir.config_parameter']
                .sudo()
                .get_param(
                    'login_whatsapp_alert.recipient_number'
                )
            )

            if not whatsapp_number:
                _logger.warning(
                    "Login WhatsApp Alert: "
                    "recipient number is not configured."
                )
                return

            # ---------------------------------------------------------
            # Create login alert record
            # ---------------------------------------------------------

            alert = request.env[
                'odoo.login.alert'
            ].sudo().create({
                'name': 'Login Alert',
                'user_id': user.id,
                'login': login or user.login,
                'ip_address': ip_address or '',
                'login_datetime': fields.Datetime.now(),
                'phone': whatsapp_number,
                'status': 'success',
                'company_id': user.company_id.id,
            })

            # ---------------------------------------------------------
            # Find WhatsApp template
            # ---------------------------------------------------------

            template = request.env[
                'whatsapp.template'
            ].sudo().search([
                ('name', '=', 'Odoo Login Alert'),
            ], limit=1)
            # ('status', '=', 'approved'),

            if not template:
                _logger.warning(
                    "Login WhatsApp Alert: "
                    "approved WhatsApp template "
                    "'doo Login Alert' was not found."
                )
                return

            # ---------------------------------------------------------
            # Verify template model
            # ---------------------------------------------------------

            if (
                template.model_id
                and template.model_id.model
                != 'odoo.login.alert'
            ):
                _logger.warning(
                    "Login WhatsApp Alert: template "
                    "'doo Login Alert' is configured for model %s "
                    "instead of odoo.login.alert.",
                    template.model_id.model,
                )
                return

            # ---------------------------------------------------------
            # Native Odoo WhatsApp Composer
            # ---------------------------------------------------------

            composer = request.env[
                'whatsapp.composer'
            ].sudo().create({
                'res_ids': str(alert.ids),
                'res_model': 'odoo.login.alert',
                'wa_template_id': template.id,
            })

            composer._send_whatsapp_template(
                force_send_by_cron=True
            )

            _logger.info(
                "Login WhatsApp Alert sent successfully. "
                "User=%s, Login=%s, IP=%s",
                user.name,
                login,
                ip_address,
            )

        except Exception:
            # WhatsApp failure should NEVER prevent
            # the user from logging into Odoo.
            _logger.exception(
                "Login WhatsApp Alert failed."
            )


    @http.route(
        '/web/login',
        type='http',
        auth='none',
        readonly=False,
        list_as_website_content=_lt("Login")
    )
    def web_login(self, redirect=None, **kw):

        ensure_db()

        request.params['login_success'] = False

        # Already logged in
        if (
            request.httprequest.method == 'GET'
            and redirect
            and request.session.uid
        ):
            return request.redirect(redirect)

        # Set authentication environment
        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(
                    user=request.session.uid
                )

        values = {
            k: v
            for k, v in request.params.items()
            if k in SIGN_UP_REQUEST_PARAMS
        }

        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        # ==========================================================
        # LOGIN
        # ==========================================================
        if request.httprequest.method == 'POST':

            login = request.params.get('login')
            password = request.params.get('password')

            # ------------------------------------------------------
            # Get user safely
            # ------------------------------------------------------
            user = request.env['res.users'].sudo().search(
                [('login', '=', login)],
                limit=1
            )

            # ------------------------------------------------------
            # Get REAL CLIENT IP
            # ------------------------------------------------------
            http_request = request.httprequest
            forwarded_for = http_request.headers.get(
                'X-Forwarded-For'
            )

            real_ip = http_request.headers.get(
                'X-Real-IP'
            )
            ip_address = False
            if forwarded_for:
                client_ip = (
                    forwarded_for
                    .split(',')[0]
                    .strip()
                )

                if client_ip:
                    ip_address = client_ip
                
            elif real_ip and ip_address == False:
                ip_address = real_ip.strip()
            else:
                ip_address = http_request.remote_addr
            
            # ip_address = request.httprequest.remote_addr

            print('\n\n===XXX=====')
            start_time = False
            end_time = False
            current_date = fields.Datetime.now() + timedelta(hours=5, minutes=30)
            if user and user.login_time and user.logout_time:
                hours = int(user.login_time)
                minutes = round((user.login_time - hours) * 60)
                start_time = current_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(hours=hours, minutes=minutes)
                x = round((user.login_time - hours) * 60),(user.login_time - hours),hours
                print('==login_time=====',x)
                _logger.warning("XXXXXXXX  %s",x,)
                hours = int(user.logout_time)
                minutes = round((user.logout_time - hours) * 60)
                end_time = current_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(hours=hours, minutes=minutes)
            
            _logger.warning("start_time  %s",start_time,)
            _logger.warning("end_time  %s",end_time,)
            _logger.warning("current_date  %s",current_date,)
            print('==start_time=====',start_time)
            print('==end_time=====',end_time)
            print('==current_date=====',current_date)
            if user.exists() and user.allowed_ip_ids:
                # Check IP
                allowed_ips = set(
                    user.allowed_ip_ids.mapped('ip_address')
                )
                if ip_address not in allowed_ips:
                    values['error'] = _(
                        'Not allowed to login from this IP.'
                    )

                # Check Time
                elif start_time and end_time and not (start_time <= current_date <= end_time):
                    values['error'] = _(
                        'Login not allowed at this time.'
                    )

                else:

                    # ----------------------------------------------
                    # Normal Odoo authentication
                    # ----------------------------------------------
                    try:

                        credential = {
                            key: value
                            for key, value in request.params.items()
                            if key in CREDENTIAL_PARAMS and value
                        }

                        credential.setdefault(
                            'type',
                            'password'
                        )

                        # CAPTCHA
                        if request.env[
                            'res.users'
                        ]._should_captcha_login(credential):

                            request.env[
                                'ir.http'
                            ]._verify_request_recaptcha_token(
                                'login'
                            )

                        # Authenticate
                        auth_info = request.session.authenticate(
                            request.env,
                            credential
                        )


                        request.params['login_success'] = True

                        # print(ddd)
                        # ---------------------------------------------------------
                        # WhatsApp alert
                        # ---------------------------------------------------------

                        self._send_login_whatsapp_alert(
                            user_id=auth_info['uid'],
                            login=login,
                            ip_address=ip_address,
                        )

                        return request.redirect(
                            self._login_redirect(
                                auth_info['uid'],
                                redirect=redirect
                            )
                        )

                    except odoo.exceptions.AccessDenied as e:

                        if (
                            e.args
                            == odoo.exceptions.AccessDenied().args
                        ):
                            values['error'] = _(
                                'Wrong login/password'
                            )
                        else:
                            values['error'] = e.args[0]

            else:

                # --------------------------------------------------
                # No IP restriction configured
                # --------------------------------------------------
                if start_time and end_time and not (start_time <= current_date <= end_time):
                    values['error'] = _(
                        'Login not allowed at this time.'
                    )
                else:
                    try:

                        credential = {
                            key: value
                            for key, value in request.params.items()
                            if key in CREDENTIAL_PARAMS and value
                        }

                        credential.setdefault(
                            'type',
                            'password'
                        )

                        # CAPTCHA
                        if request.env[
                            'res.users'
                        ]._should_captcha_login(credential):

                            request.env[
                                'ir.http'
                            ]._verify_request_recaptcha_token(
                                'login'
                            )

                        # Authenticate
                        auth_info = request.session.authenticate(
                            request.env,
                            credential
                        )

                        request.params['login_success'] = True

                        return request.redirect(
                            self._login_redirect(
                                auth_info['uid'],
                                redirect=redirect
                            )
                        )

                    except odoo.exceptions.AccessDenied as e:

                        if (
                            e.args
                            == odoo.exceptions.AccessDenied().args
                        ):
                            values['error'] = _(
                                'Wrong login/password'
                            )
                        else:
                            values['error'] = e.args[0]

        else:

            if (
                'error' in request.params
                and request.params.get('error') == 'access'
            ):
                values['error'] = _(
                    'Only employees can access this database. '
                    'Please contact the administrator.'
                )

        # Remember login
        if (
            'login' not in values
            and request.session.get('auth_login')
        ):
            values['login'] = request.session.get(
                'auth_login'
            )

        # Disable DB manager
        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        # Render login page
        response = request.render(
            'web.login',
            values
        )

        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = (
            "frame-ancestors 'self'"
        )


        return response