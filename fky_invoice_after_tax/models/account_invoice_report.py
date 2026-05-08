from odoo import models, fields

class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    price_total = fields.Float(string='Total Amount (After Tax)', readonly=True)

    def _select(self):
        select_str = super()._select()
        # Odoo's price_subtotal is calculated as `-line.balance * currency_table.rate`.
        # To get the after-tax amount (price_total) in the same currency, we can take
        # the price_total from the move_line (which is in foreign currency) and adjust it
        # based on the ratio between line.balance (company currency) and line.price_subtotal (foreign currency).
        # But simpler: we use line.balance directly for the subtotal, and scale it up by the (price_total / price_subtotal) ratio.
        # This handles currency and sign correctly!
        select_str += """,
            COALESCE(
                (-line.balance * currency_table.rate) * 
                (line.price_total / NULLIF(line.price_subtotal, 0.0)), 
                0.0
            ) AS price_total
        """
        return select_str
