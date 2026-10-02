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
    total = fields.Integer(string="Total", compute="_compute_total_packages")
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

    @api.depends("bags", "boxes")
    def _compute_total_packages(self):
        for rec in self:
            rec.total = rec.boxes + rec.bags

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