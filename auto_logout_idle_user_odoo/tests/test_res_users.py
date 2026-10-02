# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger
from psycopg2.errors import CheckViolation
import psycopg2

class TestResUsers(TransactionCase):

    def setUp(self):
        super(TestResUsers, self).setUp()
        self.User = self.env['res.users']

    def test_update_user_valid_idle_time(self):
        """Test updating a user with a valid idle time"""
        user = self.env.user
        user.write({
            'enable_idle': True,
            'idle_time': 15,
        })
        self.env.flush_all()
        self.assertEqual(user.idle_time, 15, "Idle time should be set correctly.")
        self.assertTrue(user.enable_idle, "Enable idle should be True.")

    @mute_logger('odoo.sql_db')
    def test_update_user_invalid_idle_time(self):
        """Test updating a user with an invalid idle time (< 1)"""
        user = self.env.user
        with self.assertRaises(Exception):
            user.write({
                'enable_idle': True,
                'idle_time': 0,
            })
            self.env.flush_all()

    @mute_logger('odoo.sql_db')
    def test_update_user_negative_idle_time(self):
        """Test updating a user with a negative idle time"""
        user = self.env.user
        with self.assertRaises(Exception):
            user.write({
                'enable_idle': True,
                'idle_time': -5,
            })
            self.env.flush_all()
