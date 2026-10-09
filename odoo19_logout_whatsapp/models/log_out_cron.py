
import glob
import logging
import os
from datetime import time, timedelta
from odoo import api, fields, models
from odoo.http import root

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    logout_time_last_date = fields.Date(
        string="Last Scheduled Logout Date",
        copy=False,
        readonly=True,
    )

    # @api.model
    def _cron_auto_logout_users(self):
        """Log users out of all matching Odoo sessions at logout_time."""
        now_utc = fields.Datetime.now()
        users = self.sudo().search([
            ("logout_time", ">", 0),
            ("active", "=", True),
        ])

        for user in users:
            current_date = fields.Datetime.now() + timedelta(hours=5, minutes=30)
            hours = int(user.logout_time)
            minutes = round((user.logout_time - hours) * 60)
            end_time = current_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(hours=hours, minutes=minutes)
            
            _logger.warning("end_time  %s",end_time,)
            _logger.warning("current_date  %s",current_date,)
            print('==end_time=====',end_time)
            print('==current_date=====',current_date)
            if current_date > end_time: 
                # print('\n\n===',xx)
                self._invalidate_user_sessions(
                    user_id=user,
                    database=self.env.cr.dbname,
                )

    # @api.model
    def direct_run_invalidate_user_sessions(self):
        print('\n\n==self.env.cr.dbname=',self.env.cr.dbname)
        self._invalidate_user_sessions(user_id=self,database=self.env.cr.dbname)

    def _invalidate_user_sessions(self, user_id, database):
        """Invalidate all filesystem sessions for a user in this DB."""
        store = root.session_store

        if not hasattr(store, "path") or not hasattr(
            store, "delete_from_identifiers"
        ):
            raise RuntimeError(
                "Unsupported Odoo session store. "
                "Configure session invalidation for this backend."
            )

        session_files = glob.iglob(
            os.path.join(store.path, "*", "*")
        )
        identifiers = set()

        for filepath in session_files:
            sid = os.path.basename(filepath)

            try:
                user_id._send_logout_whatsapp_notification()
                session = store.get(sid)

                if (
                    session
                    and session.get("uid") == user_id.id
                    and session.get("db") == database
                ):
                    # Odoo 19 associates rotated session IDs through
                    # the stored identifier prefix.
                    identifiers.add(sid[:42])

            except (OSError, ValueError, KeyError):
                _logger.debug(
                    "Could not inspect session file %s",
                    filepath,
                    exc_info=True,
                )

        if identifiers:
            store.delete_from_identifiers(list(identifiers))

            _logger.info(
                "Invalidated %s session identifier(s) for user ID %s",
                len(identifiers),
                user_id.id,
            )