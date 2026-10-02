from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    available_transporter_ids = fields.Many2many(
            "res.partner",
            compute="_compute_available_transporters",
        )
        
    transporter_id = fields.Many2one(
            "res.partner",
            string="Transporter",
            domain="[('id', 'in', available_transporter_ids)]",
            readonly=True,
        )
    booking_name = fields.Char(string="Booking Name")
    lr_no = fields.Char(string="LR No")
    lr_date = fields.Date(string="LR Date")
    vehicle_num = fields.Char(string="Vehicle No")
    boxes = fields.Integer(string="Boxes")
    bags = fields.Integer(string="Bags")
    total = fields.Float(
        string="Total Packages",
        compute="_compute_total_packages",
        store=True,
    )
    kppl_number = fields.Char(string="KPPL order No.")  

    whatsapp_sent = fields.Boolean(
        string="WhatsApp Sent",
        default=False,
        copy=False,
    )  
    

    @api.depends("partner_id")
    def _compute_available_transporters(self):
        for rec in self:
            rec.available_transporter_ids = rec.partner_id.transporter_ids

    @api.depends("invoice_line_ids.sale_line_ids.total_pkgs")
    def _compute_total_packages(self):
        for move in self:
            sale_lines = move.invoice_line_ids.mapped("sale_line_ids")
            move.total = sum(sale_lines.mapped("total_pkgs"))

    def action_generate_einvoice(self):
        self.ensure_one()

        # Generate E-Invoice
        result = self._l10n_in_edi_send_invoice()

        # If there were validation/API errors, stop here
        if result:
            return result

        # Generate E-Waybill
        ewaybill = self.l10n_in_ewaybill_ids[:1]
        if ewaybill and ewaybill.state == "pending":
            ewaybill.action_generate_ewaybill()

        return True

    def action_open_whatsapp_composer(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Send WhatsApp Message"),
            "res_model": "whatsapp.composer",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "active_ids": self.ids,
            },
        }

    def action_post(self):
        for move in self:
            if move.move_type in ("out_invoice", "out_refund"):
                partner = move.partner_id.commercial_partner_id

                if (
                    partner.company_type == "company"
                    and not partner.phone
                ):
                    raise ValidationError(
                        _(
                            "Phone Number is required for Company type partners.\n\n"
                            "Please add a phone number for %s before confirming the invoice."
                        )
                        % partner.display_name
                    )

        return super().action_post()