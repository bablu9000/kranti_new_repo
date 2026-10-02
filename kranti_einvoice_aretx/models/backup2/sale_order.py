from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Sale order stage renaming to Dispatch Order  
    state = fields.Selection(
        selection=[
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Dispatch Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
    )

    boxes = fields.Integer(string="Boxes")
    bags = fields.Integer(string="Bags")
    total = fields.Float(
        string="Total Packages",
        compute="_compute_total_packages",
        store=True,
    )

    available_transporter_ids = fields.Many2many(
        "res.partner",
        compute="_compute_available_transporters",
    )

    transporter_id = fields.Many2one(
        "res.partner",
        string="Transporter",
        domain="[('id', 'in', available_transporter_ids)]",
    )

    booking_name = fields.Char(string="Booking Name", related="partner_id.booking_name", readonly=False)

    kppl_number = fields.Char(string="KPPL order No.")

    def _search(self, domain, *args, **kwargs):
        if self.env.user.has_group(
            "kranti_einvoice_aretx.group_hide_fully_invoiced_sale_orders"
        ):
            domain = list(domain or [])
            domain.append(("invoice_status", "!=", "invoiced"))

        return super()._search(domain, *args, **kwargs)

    @api.depends("partner_id")
    def _compute_available_transporters(self):
        for rec in self:
            rec.available_transporter_ids = rec.partner_id.transporter_ids

    @api.onchange("partner_id")
    def _onchange_partner_id_transporter(self):
        for rec in self:
            partner = rec.partner_id

            if not partner:
                rec.transporter_id = False
                continue

            if partner.default_transporter_id:
                rec.transporter_id = partner.default_transporter_id

            elif partner.transporter_ids:
                rec.transporter_id = partner.transporter_ids[0]

            else:
                rec.transporter_id = False


    @api.onchange("transporter_id")
    def _onchange_transporter_id(self):
        for rec in self:
            if rec.partner_id and rec.transporter_id:
                rec.partner_id.default_transporter_id = rec.transporter_id


    def write(self, vals):
        _logger.error("========== SALE ORDER WRITE CALLED ==========")
        _logger.error("SO vals: %s", vals)

        res = super().write(vals)

        if "transporter_id" in vals:
            for order in self:
                _logger.error(
                    "SO %s transporter changed to %s (%s)",
                    order.name,
                    order.transporter_id.name,
                    order.transporter_id.id,
                )

                # Save latest transporter for customer
                if order.partner_id and order.transporter_id:
                    order.partner_id.write({
                        "default_transporter_id": order.transporter_id.id
                    })

                # SO → Invoice
                invoices = order.invoice_ids

                _logger.error(
                    "Invoices found: %s",
                    invoices.mapped("name"),
                )

                invoices.write({
                    "transporter_id": order.transporter_id.id,
                })

                # SO → E-Way Bill
                ewaybills = invoices.mapped("l10n_in_ewaybill_ids")

                _logger.error(
                    "E-Way Bills found: %s",
                    ewaybills.mapped("name"),
                )

                _logger.error(
                    "E-Way Bill current transporters: %s",
                    ewaybills.mapped("transporter_id.name"),
                )

                ewaybills.write({
                    "transporter_id": order.transporter_id.id,
                })

                _logger.error(
                    "E-Way Bill after write: %s",
                    ewaybills.mapped("transporter_id.name"),
                )

        return res

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()

        vals.update({
            "transporter_id": self.transporter_id.id,
            "booking_name": self.booking_name,
            "kppl_number": self.kppl_number,
            "boxes": self.boxes,
            "bags": self.bags,
            "total": self.total,
        })

        return vals


    @api.depends("order_line.total_pkgs")
    def _compute_total_packages(self):
        for rec in self:
            rec.total = sum(rec.order_line.mapped("total_pkgs"))

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