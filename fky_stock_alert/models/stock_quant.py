from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_stock_alert_rules()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ['quantity', 'product_id', 'location_id']):
            self._update_stock_alert_rules()
        return res

    def unlink(self):
        # Gather product and location ids before they are deleted
        products = self.mapped('product_id').ids
        locations = self.mapped('location_id').ids
        res = super().unlink()
        
        # Trigger update on rules matching the deleted quants
        if products and locations:
            rules = self.env['stock.alert.rule'].sudo().search([
                ('product_id', 'in', products),
                ('location_id', 'in', locations),
            ])
            for rule in rules:
                rule._compute_qty()
                rule.sudo().write({
                    'qty_available': rule.qty_available,
                    'state': rule.state,
                })
        return res

    def _update_stock_alert_rules(self):
        products = self.mapped('product_id').ids
        locations = self.mapped('location_id').ids
        if products and locations:
            rules = self.env['stock.alert.rule'].sudo().search([
                ('product_id', 'in', products),
                ('location_id', 'in', locations),
            ])
            for rule in rules:
                rule._compute_qty()
                rule.sudo().write({
                    'qty_available': rule.qty_available,
                    'state': rule.state,
                })
