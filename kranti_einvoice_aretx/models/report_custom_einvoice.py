import base64
import json
from io import BytesIO

import qrcode

from odoo import api, models


class ReportCustomEinvoice(models.AbstractModel):
    _name = "report.kranti_einvoice_aretx.report_custom_einvoice"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["account.move"].browse(docids)

        einvoice_json = {}
        qr_base64 = False

        attachment = self.env["ir.attachment"].search([
            ("res_model", "=", "account.move"),
            ("res_id", "=", docs.id),
            ("name", "ilike", "_einvoice"),
        ], limit=1)

        if attachment:
            decoded = base64.b64decode(attachment.datas).decode("utf-8")
            einvoice_json = json.loads(decoded)

            signed_qr = einvoice_json.get("SignedQRCode")
            if signed_qr:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8,
                    border=2,
                )
                qr.add_data(signed_qr)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")

                buffer = BytesIO()
                img.save(buffer, format="PNG")

                qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "doc_ids": docids,
            "doc_model": "account.move",
            "docs": docs,
            "l10n_in_einvoice_json": einvoice_json,
            "qr_base64": qr_base64,
        }