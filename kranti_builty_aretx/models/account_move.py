from odoo import fields, models, _
from odoo.exceptions import UserError
import base64


class AccountMove(models.Model):
    _inherit = "account.move"

    builty_image = fields.Image(
        string="Builty Image",
        attachment=True,
    )

    def action_whatsapp_builty(self):
        self.ensure_one()

        if not self.builty_image:
            raise UserError(
                _("Please upload a Builty Image before sending it on WhatsApp.")
            )

        if not self.partner_id:
            raise UserError(
                _("Please select a customer before sending the Builty.")
            )

        # Find the Builty WhatsApp template
        template = self.env["whatsapp.template"].search(
            [
                ("name", "=", "Builty Sending"),
                ("model", "=", "account.move"),
            ],
            limit=1,
        )

        if not template:
            raise UserError(
                _("The 'Builty Sending' WhatsApp template was not found.")
            )

        # Generate the Builty PDF
        pdf_content, content_type = self.env[
            "ir.actions.report"
        ]._render_qweb_pdf(
            "kranti_builty_aretx.builty_report_document",
            self.ids,
        )

        # Create the Builty PDF attachment
        attachment = self.env["ir.attachment"].create({
            "name": "%s - Builty.pdf" % self.name,
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "res_model": "account.move",
            "res_id": self.id,
            "mimetype": "application/pdf",
        })

        # Open WhatsApp composer with the Builty template
        composer = self.env["whatsapp.composer"].with_context(
            active_model="account.move",
            active_id=self.id,
            active_ids=self.ids,
        ).create({
            "res_model": "account.move",
            "res_ids": str(self.ids),
            "wa_template_id": template.id,
            "attachment_id": attachment.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Send Builty via WhatsApp"),
            "res_model": "whatsapp.composer",
            "view_mode": "form",
            "views": [(False, "form")],
            "res_id": composer.id,
            "target": "new",
        }