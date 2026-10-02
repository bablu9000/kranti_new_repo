# -*- coding: utf-8 -*-

import odoo

from odoo import http
from odoo.addons.web.controllers import home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.http import request
from odoo.tools.translate import LazyTranslate, _
import socket

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
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address=s.getsockname()[0]
            s.close()
            
            # ip_address = request.httprequest.remote_addr

            # ------------------------------------------------------
            # IP RESTRICTION
            #
            # If allowed_ip_ids are configured:
            #     only those IPs can login.
            #
            # If no allowed IP is configured:
            #     normal login is allowed.
            # ------------------------------------------------------
            if user.exists() and user.allowed_ip_ids:

                allowed_ips = set(
                    user.allowed_ip_ids.mapped('ip_address')
                )

                if ip_address not in allowed_ips:

                    values['error'] = _(
                        'Not allowed to login from this IP.'
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