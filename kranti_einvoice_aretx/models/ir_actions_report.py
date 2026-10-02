from odoo import models
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report_name = report_ref

        # report_ref can sometimes be a report record
        if not isinstance(report_ref, str):
            report_name = report_ref.report_name

        if report_name == "kranti_einvoice_aretx.report_custom_ewaybill_document":
            moves = self.env["account.move"].browse(res_ids)

            for move in moves:
                ewaybill = self.env["l10n.in.ewaybill"].search(
                    [("account_move_id", "=", move.id)],
                    limit=1,
                )

                if not ewaybill:
                    raise UserError(
                        "Please create the E-Way Bill before printing this report."
                    )

        return super()._render_qweb_pdf(
            report_ref,
            res_ids=res_ids,
            data=data,
        )