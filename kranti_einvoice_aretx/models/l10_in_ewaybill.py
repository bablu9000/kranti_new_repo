from odoo import models, fields, api

class L10nInEwaybill(models.Model):
    _inherit = "l10n.in.ewaybill"

    available_transporter_ids = fields.Many2many(
        "res.partner",
        compute="_compute_available_transporters",
    )

    mode = fields.Selection(
        selection=[
            ("1", "By Road"),
            ("2", "Rail"),
            ("3", "Air"),
            ("4", "Ship or Ship Cum Road/Rail"),
        ],
        string="Transportation Mode",
        copy=False,
        tracking=True,
        default=None,
    )

    # -------------------------------------------------------------------------
    # AVAILABLE TRANSPORTERS
    # -------------------------------------------------------------------------

    @api.depends("partner_bill_to_id")
    def _compute_available_transporters(self):
        for rec in self:
            if rec.partner_bill_to_id:
                rec.available_transporter_ids = (
                    rec.partner_bill_to_id.transporter_ids
                )
            else:
                rec.available_transporter_ids = False

    # -------------------------------------------------------------------------
    # GET PREVIOUS DISTANCE FOR TRANSPORTER + CUSTOMER
    # -------------------------------------------------------------------------

    def _get_previous_transporter_customer_distance(self):
        self.ensure_one()

        if not self.transporter_id or not self.partner_bill_to_id:
            return 0

        transporter = self.transporter_id.commercial_partner_id
        customer = self.partner_bill_to_id.commercial_partner_id

        history = self.env["ewaybill.transporter.customer"].search(
            [
                ("transporter_id", "=", transporter.id),
                ("customer_id", "=", customer.id),
            ],
            limit=1,
        )

        return history.last_distance if history else 0

    # -------------------------------------------------------------------------
    # SAVE / UPDATE TRANSPORTER + CUSTOMER DISTANCE HISTORY
    # -------------------------------------------------------------------------

    def _save_transporter_customer_distance(self):
        History = self.env["ewaybill.transporter.customer"]

        for rec in self:
            if not rec.transporter_id or not rec.partner_bill_to_id:
                continue

            # Do not save zero as the latest meaningful distance.
            if not rec.distance or rec.distance <= 0:
                continue

            transporter = rec.transporter_id.commercial_partner_id
            customer = rec.partner_bill_to_id.commercial_partner_id

            history = History.search(
                [
                    ("transporter_id", "=", transporter.id),
                    ("customer_id", "=", customer.id),
                ],
                limit=1,
            )

            if history:
                history.write({
                    "last_distance": rec.distance,
                })
            else:
                History.create({
                    "transporter_id": transporter.id,
                    "customer_id": customer.id,
                    "last_distance": rec.distance,
                })

    # -------------------------------------------------------------------------
    # BILL TO CUSTOMER CHANGED
    # -------------------------------------------------------------------------

    @api.onchange("partner_bill_to_id")
    def _onchange_partner_bill_to_id(self):
        for rec in self:
            partner = rec.partner_bill_to_id

            if not partner:
                continue

            # Existing transporter selection logic
            if partner.default_transporter_id:
                rec.transporter_id = partner.default_transporter_id

            elif partner.transporter_ids:
                rec.transporter_id = partner.transporter_ids[0]

            # If transporter is available, load its previous distance
            if rec.transporter_id:
                rec.distance = rec._get_previous_transporter_customer_distance()

    # -------------------------------------------------------------------------
    # TRANSPORTER CHANGED
    # -------------------------------------------------------------------------

    @api.onchange("transporter_id")
    def _onchange_transporter_id(self):
        for rec in self:
            if not rec.transporter_id:
                continue

            # -------------------------------------------------------------
            # Existing logic:
            # Save selected transporter as customer's default transporter
            # -------------------------------------------------------------

            if rec.partner_bill_to_id:
                rec.partner_bill_to_id.default_transporter_id = (
                    rec.transporter_id
                )

            # -------------------------------------------------------------
            # NEW LOGIC:
            # Find previous distance for this exact:
            #
            # Transporter + Customer
            #
            # combination.
            # -------------------------------------------------------------

            if rec.partner_bill_to_id:
                rec.distance = (
                    rec._get_previous_transporter_customer_distance()
                )

            # -------------------------------------------------------------
            # Existing invoice / sale order transporter synchronization
            # -------------------------------------------------------------

            invoice = rec.account_move_id

            if not invoice:
                continue

            # E-Way Bill → Invoice
            invoice.transporter_id = rec.transporter_id

            # Invoice → Sale Order
            sale_orders = invoice.invoice_line_ids.mapped(
                "sale_line_ids.order_id"
            )

            if sale_orders:
                sale_orders.transporter_id = rec.transporter_id

    # -------------------------------------------------------------------------
    # UPDATE INVOICE TRANSPORT DETAILS
    # -------------------------------------------------------------------------

    def _update_invoice_transport_details(self):
        for rec in self:
            if rec.account_move_id and rec.transportation_doc_no:
                vehicle_type = dict(
                    rec._fields["vehicle_type"].selection
                ).get(
                    rec.vehicle_type,
                    "",
                )

                rec.account_move_id.write({
                    "vehicle_num": rec.vehicle_no or "",
                    "vehicle_type": vehicle_type,
                })

    # -------------------------------------------------------------------------
    # UPDATE SALE ORDER + INVOICE TRANSPORTER
    # -------------------------------------------------------------------------

    def _update_sale_order_and_invoice_transporter(self):
        for rec in self:
            if not rec.account_move_id or not rec.transporter_id:
                continue

            invoice = rec.account_move_id

            # E-Way Bill → Invoice
            invoice.write({
                "transporter_id": rec.transporter_id.id,
            })

            # E-Way Bill → Sale Order
            sale_orders = invoice.invoice_line_ids.mapped(
                "sale_line_ids.order_id"
            )

            if sale_orders:
                sale_orders.write({
                    "transporter_id": rec.transporter_id.id,
                })

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:

            # -------------------------------------------------------------
            # Determine transporter from Sale Order first
            # -------------------------------------------------------------

            if rec.account_move_id:
                sale_orders = rec.account_move_id.invoice_line_ids.mapped(
                    "sale_line_ids.order_id"
                )

                if sale_orders and sale_orders[0].transporter_id:
                    rec.transporter_id = sale_orders[0].transporter_id

            # -------------------------------------------------------------
            # Otherwise use customer's default transporter
            # -------------------------------------------------------------

            if not rec.transporter_id and rec.partner_bill_to_id:
                partner = rec.partner_bill_to_id

                if partner.default_transporter_id:
                    rec.transporter_id = (
                        partner.default_transporter_id
                    )

                elif partner.transporter_ids:
                    rec.transporter_id = partner.transporter_ids[0]

            # -------------------------------------------------------------
            # If distance wasn't explicitly provided, load previous KM
            # -------------------------------------------------------------

            if (
                rec.transporter_id
                and rec.partner_bill_to_id
                and not rec.distance
            ):
                previous_distance = (
                    rec._get_previous_transporter_customer_distance()
                )

                if previous_distance:
                    rec.distance = previous_distance

            # -------------------------------------------------------------
            # Update invoice details
            # -------------------------------------------------------------

            rec._update_invoice_transport_details()

        # -------------------------------------------------------------
        # Save current distance as latest history
        # -------------------------------------------------------------

        records._save_transporter_customer_distance()

        return records

    # -------------------------------------------------------------------------
    # WRITE
    # -------------------------------------------------------------------------

    def write(self, vals):
        result = super().write(vals)

        # -------------------------------------------------------------
        # Transporter changed
        # -------------------------------------------------------------

        if "transporter_id" in vals:
            for rec in self:
                if rec.partner_bill_to_id and rec.transporter_id:
                    rec.partner_bill_to_id.write({
                        "default_transporter_id": rec.transporter_id.id,
                    })

        # -------------------------------------------------------------
        # Vehicle details changed
        # -------------------------------------------------------------

        if any(
            field in vals
            for field in (
                "vehicle_no",
                "vehicle_type",
                "transportation_doc_no",
            )
        ):
            self._update_invoice_transport_details()

        # -------------------------------------------------------------
        # Distance / transporter / customer changed
        #
        # Update the latest KM for this exact transporter + customer.
        # -------------------------------------------------------------

        if any(
            field in vals
            for field in (
                "distance",
                "transporter_id",
                "partner_bill_to_id",
            )
        ):
            self._save_transporter_customer_distance()

        return result

    # -------------------------------------------------------------------------
    # QR CODE DATA
    # -------------------------------------------------------------------------

    def _get_ewaybill_qr_data(self):
        self.ensure_one()

        date = (
            self.ewaybill_date.strftime("%d-%b-%Y %I:%M %p")
            if self.ewaybill_date
            else ""
        )

        return (
            f"EWB No.: {self.name or ''} / "
            f"GSTIN: {self.company_id.vat or ''} / "
            f"Date: {date}"
        )


#  from odoo import models, fields, api


# class L10nInEwaybill(models.Model):
#     _inherit = "l10n.in.ewaybill"

#     available_transporter_ids = fields.Many2many(
#         "res.partner",
#         compute="_compute_available_transporters",
#     )

#     mode = fields.Selection(
#         selection=[
#             ('1', 'By Road'),
#             ('2', 'Rail'),
#             ('3', 'Air'),
#             ('4', 'Ship or Ship Cum Road/Rail'),

#         ],
#         string="Transportation Mode",
#         copy=False,
#         tracking=True,
#         default=None,
#     )

#     @api.onchange("partner_bill_to_id")
#     def _onchange_partner_bill_to_id(self):
#         for rec in self:
#             partner = rec.partner_bill_to_id

#             if not partner:
#                 continue

#             if partner.default_transporter_id:
#                 rec.transporter_id = partner.default_transporter_id

#             elif partner.transporter_ids:
#                 rec.transporter_id = partner.transporter_ids[0]

#     @api.depends("partner_bill_to_id")
#     def _compute_available_transporters(self):
#         for rec in self:
#             rec.available_transporter_ids = (
#                 rec.partner_bill_to_id.transporter_ids
#             )

#     @api.onchange("transporter_id")
#     def _onchange_transporter_id(self):
#         for rec in self:
#             if rec.partner_bill_to_id and rec.transporter_id:
#                 rec.partner_bill_to_id.default_transporter_id = rec.transporter_id

#     def _update_invoice_transport_details(self):
#         for rec in self:
#             if rec.account_move_id and rec.transportation_doc_no:
#                 vehicle_type = dict(
#                     rec._fields["vehicle_type"].selection
#                 ).get(rec.vehicle_type, "")

#                 rec.account_move_id.write({
#                     "vehicle_num": rec.vehicle_no or "",
#                     "vehicle_type": vehicle_type,
#                 })
#     @api.onchange("transporter_id")
#     def _onchange_transporter_id(self):
#         for rec in self:
#             if rec.partner_bill_to_id and rec.transporter_id:
#                 rec.partner_bill_to_id.default_transporter_id = rec.transporter_id

#     @api.onchange("transporter_id")
#     def _onchange_transporter_id(self):
#         for rec in self:
#             if not rec.transporter_id:
#                 continue

#             # Save latest transporter for the partner
#             if rec.partner_bill_to_id:
#                 rec.partner_bill_to_id.default_transporter_id = rec.transporter_id

#             # Get the linked invoice
#             invoice = rec.account_move_id

#             if not invoice:
#                 continue

#             # E-Way Bill → Invoice
#             invoice.transporter_id = rec.transporter_id

#             # Invoice → Sale Order
#             sale_orders = invoice.invoice_line_ids.mapped(
#                 "sale_line_ids.order_id"
#             )

#             sale_orders.transporter_id = rec.transporter_id

#     def _update_sale_order_and_invoice_transporter(self):
#         for rec in self:
#             if not rec.account_move_id or not rec.transporter_id:
#                 continue

#             invoice = rec.account_move_id

#             # E-Way Bill → Invoice
#             invoice.write({
#                 "transporter_id": rec.transporter_id.id,
#             })

#             # E-Way Bill → Sale Order
#             sale_orders = invoice.invoice_line_ids.mapped(
#                 "sale_line_ids.order_id"
#             )

#             sale_orders.write({
#                 "transporter_id": rec.transporter_id.id,
#             })


#     @api.model_create_multi
#     def create(self, vals_list):
#         records = super().create(vals_list)

#         for rec in records:
#             sale_orders = rec.account_move_id.invoice_line_ids.mapped(
#                 "sale_line_ids.order_id"
#             )

#             if sale_orders:
#                 rec.transporter_id = sale_orders[0].transporter_id

#             elif rec.partner_bill_to_id:
#                 partner = rec.partner_bill_to_id

#                 if partner.default_transporter_id:
#                     rec.transporter_id = partner.default_transporter_id

#                 elif partner.transporter_ids:
#                     rec.transporter_id = partner.transporter_ids[0]

#         records._update_invoice_transport_details()
#         return records

#     def write(self, vals):
#         res = super().write(vals)

#         if "transporter_id" in vals:
#             for rec in self:
#                 if rec.partner_bill_to_id and rec.transporter_id:
#                     rec.partner_bill_to_id.write({
#                         "default_transporter_id": rec.transporter_id.id
#                     })

#         if any(field in vals for field in (
#             "vehicle_no",
#             "vehicle_type",
#             "transportation_doc_no",
#         )):
#             self._update_invoice_transport_details()

#         return res

#     def _get_ewaybill_qr_data(self):
#         self.ensure_one()

#         date = (
#             self.ewaybill_date.strftime("%d-%b-%Y %I:%M %p")
#             if self.ewaybill_date
#             else ""
#         )

#         return (
#             f"EWB No.: {self.name or ''} / "
#             f"GSTIN: {self.company_id.vat or ''} / "
#             f"Date: {date}"
#         )


