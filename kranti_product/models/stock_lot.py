import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_print_custom_label(self):
        self.ensure_one()
        _logger.warning("=== KRANTI LABEL ===")
        _logger.warning("lot: %s | product: %s", self.name, self.product_id.display_name)
        for fld in ['image_1920', 'image_variant_1920']:
            val = self.product_id[fld]
            _logger.warning("  product.%s: has=%s type=%s len=%s preview=%s",
                fld, bool(val), type(val).__name__ if val is not False else 'None',
                len(val) if val and not isinstance(val, bool) else 0,
                (val[:60] if val and not isinstance(val, bool) else 'N/A'))
        val = self.product_id.product_tmpl_id.image_1920
        _logger.warning("  product.product_tmpl_id.image_1920: has=%s type=%s len=%s preview=%s",
            bool(val), type(val).__name__ if val is not False else 'None',
            len(val) if val and not isinstance(val, bool) else 0,
            (val[:60] if val and not isinstance(val, bool) else 'N/A'))
        return self.env.ref('kranti_product.action_report_custom_label').report_action(self)


