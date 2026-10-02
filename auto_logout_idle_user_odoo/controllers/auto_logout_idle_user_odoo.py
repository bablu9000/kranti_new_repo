# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class EasyLanguageSelector(http.Controller):
    """
    The EasyLanguageSelector passing minute that selected in the  login user
    account.

        Methods:
            get_idle_time(self):
                when the page is loaded adding total activated languages options
                 to the selection field.
                return a list variable.
    """

    @http.route('/get_idle_time/timer', auth='public', type='jsonrpc')
    def get_idle_time(self):
        """
        Summery:
            Getting value that selected from the login user account and pass it
            to the js function.
        return:
            type:It is a variable, that contain selected minutes.
        """
        if request.env.user.enable_idle:
            return request.env.user.idle_time
