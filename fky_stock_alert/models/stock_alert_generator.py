# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockAlertGenerator(models.TransientModel):
    _name = 'stock.alert.generator'
    _description = 'Generate Stock Alert Rules'

    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        domain=[('complete_name', 'in', ['TKADR/Stock', 'GDADR/Stock'])],
    )

    def action_generate_rules(self):
        self.ensure_one()
        # Find all active, saleable products
        products = self.env['product.product'].search([
            ('active', '=', True),
            ('sale_ok', '=', True),
        ])
        
        # Find existing rules for this location
        existing_rules = self.env['stock.alert.rule'].search([
            ('location_id', '=', self.location_id.id),
        ])
        existing_product_ids = set(existing_rules.mapped('product_id.id'))
        
        # Create rules for products that do not have them
        vals_list = []
        for product in products:
            if product.id not in existing_product_ids:
                min_qty = product.isi_perdus if (hasattr(product, 'isi_perdus') and product.isi_perdus > 0.0) else 1.0
                vals_list.append({
                    'product_id': product.id,
                    'location_id': self.location_id.id,
                    'min_qty': min_qty,
                })
        
        if vals_list:
            self.env['stock.alert.rule'].create(vals_list)
            
        # Return action to reload and view rules grouped by location
        action = self.env["ir.actions.actions"]._for_xml_id("fky_stock_alert.action_stock_alert")
        action['domain'] = []
        action['context'] = {'search_default_group_location': 1, 'search_default_low_stock': 0}
        return action
