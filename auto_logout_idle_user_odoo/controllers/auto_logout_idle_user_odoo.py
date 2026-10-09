# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


# class EasyLanguageSelector(http.Controller):
#     """
#     The EasyLanguageSelector passing minute that selected in the  login user
#     account.

#         Methods:
#             get_idle_time(self):
#                 when the page is loaded adding total activated languages options
#                  to the selection field.
#                 return a list variable.
#     """

#     @http.route('/get_idle_time/timer', auth='public', type='jsonrpc')
#     def get_idle_time(self):
#         """
#         Summery:
#             Getting value that selected from the login user account and pass it
#             to the js function.
#         return:
#         """
#         if request.env.user.enable_idle:
#             return request.env.user.idle_time

from datetime import datetime, time, timedelta

from odoo import http, fields


class AutoLogoutController(http.Controller):

    @http.route(
        '/get_logout_time/timer',
        type='json',
        auth='user',
    )
    def get_logout_time(self):
        user = request.env.user
        logout_time = user.logout_time

        if not logout_time:
            return False

        # Interpret 5.3 as 05:30, not 5.3 decimal hours.
        hours = int(logout_time)
        minutes = round((logout_time - hours) * 60)

        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            return False

        # Use the user's timezone.
        now = fields.Datetime.context_timestamp(
            user, fields.Datetime.now()
        )
        deadline = datetime.combine(
            now.date(), time(hour=hours, minute=minutes)
        )

        # If today's logout time has passed, use tomorrow's time.
        if now.replace(tzinfo=None) >= deadline:
            deadline += timedelta(days=1)

        return deadline.isoformat()
