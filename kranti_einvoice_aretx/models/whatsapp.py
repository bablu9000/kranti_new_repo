from odoo import models, _
from odoo.exceptions import UserError
import base64


class AccountReport(models.Model):
    _inherit = "account.report"

    def action_send_partner_ledger_whatsapp(self, options, params):
        # ---------------------------------------------------------
        # 1. Get the Partner Ledger line ID
        # ---------------------------------------------------------

        line_id = params.get("id")

        if not line_id:
            raise UserError(
                _("Could not determine the partner from the Partner Ledger.")
            )

        # ---------------------------------------------------------
        # 2. Extract partner ID from the Partner Ledger line ID
        # ---------------------------------------------------------

        try:
            partner_id = int(str(line_id).split("~")[-1])
        except (ValueError, TypeError):
            raise UserError(
                _("Could not determine the partner from the Partner Ledger.")
            )

        partner = self.env["res.partner"].browse(partner_id)

        if not partner.exists():
            raise UserError(
                _("The selected partner could not be found.")
            )

        # ---------------------------------------------------------
        # 3. Check phone number
        # ---------------------------------------------------------

        if not partner.phone and not partner.mobile:
            raise UserError(
                _("Please set a phone number or mobile for this partner.")
            )

        # ---------------------------------------------------------
        # 4. Prepare Partner Ledger options
        # ---------------------------------------------------------

        report = self

        options = report.get_options(previous_options=options)

        options.update({
            "partner_ids": [partner.id],
            "filter_partner_ids": [partner.id],
            "selected_partner_ids": [partner.id],
            "unfold_all": True,
        })

        # ---------------------------------------------------------
        # 5. Check whether ledger entries exist
        # ---------------------------------------------------------

        lines = report._get_lines(options)

        if len(lines) <= 1:
            raise UserError(
                _("No ledger found for this partner.")
            )

        # ---------------------------------------------------------
        # 6. Generate Partner Ledger PDF
        # ---------------------------------------------------------

        pdf_result = report.export_to_pdf(options)

        pdf_content = pdf_result.get("file_content")

        if not pdf_content:
            raise UserError(
                _("Unable to generate Partner Ledger PDF.")
            )

        file_name = f"{partner.name} - Partner Ledger.pdf"

        # ---------------------------------------------------------
        # 7. Create PDF attachment
        # ---------------------------------------------------------

        attachment = self.env["ir.attachment"].create({
            "name": file_name,
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "mimetype": "application/pdf",
            "res_model": "res.partner",
            "res_id": partner.id,
        })

        # ---------------------------------------------------------
        # 8. Find Odoo's native WhatsApp template for Contacts
        # ---------------------------------------------------------

        template = self.env["whatsapp.template"].search([
            ("model", "=", "res.partner"),
        ], limit=1)

        if not template:
            raise UserError(
                _(
                    "No WhatsApp template was found for Contacts. "
                    "Please create a WhatsApp template for the Contact "
                    "model first."
                )
            )

        # ---------------------------------------------------------
        # 9. Create native Odoo WhatsApp composer
        # ---------------------------------------------------------

        composer = self.env["whatsapp.composer"].with_context(
            active_model="res.partner",
            active_id=partner.id,
            active_ids=[partner.id],
        ).create({
            "wa_template_id": template.id,
        })

        # ---------------------------------------------------------
        # 10. Attach Partner Ledger PDF
        # ---------------------------------------------------------

        composer.attachment_ids = [(6, 0, [attachment.id])]

        # ---------------------------------------------------------
        # 11. Open native Odoo WhatsApp composer
        # ---------------------------------------------------------

        return {
            "type": "ir.actions.act_window",
            "name": _("Send WhatsApp Message"),
            "res_model": "whatsapp.composer",
            "view_mode": "form",
            "res_id": composer.id,
            "target": "new",
        }
        