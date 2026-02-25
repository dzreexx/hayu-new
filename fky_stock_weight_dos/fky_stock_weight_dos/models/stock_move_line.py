from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    estimated_weight_dos = fields.Float(string='Estimated Weight', compute='_compute_estimated_weight_dos', store=True)
    total_weight_dos = fields.Float(string='Total Weight', compute='_compute_total_weight_dos', store=True)
    
    @api.depends('product_uom_qty', 'product_id.isi_perdus', 'product_id.weight')
    def _compute_estimated_weight_dos(self):
        for line in self:
            if line.product_id and line.product_id.isi_perdus:
                 # Logic: (Reserved Qty / Isi Per Dus) * Weight
                 # This shows expected weight based on demand/reservation
                 line.estimated_weight_dos = (line.product_uom_qty / line.product_id.isi_perdus) * line.product_id.weight
            else:
                 line.estimated_weight_dos = 0.0
    
    @api.depends('qty_done', 'product_id.isi_perdus', 'product_id.weight')
    def _compute_total_weight_dos(self):
        for line in self:
            if line.product_id and line.product_id.isi_perdus:
                 # Logic: (Qty Done / Isi Per Dus) * Weight (from Odoo default)
                 # Weight in Odoo represents weight per unit/dos
                 line.total_weight_dos = (line.qty_done / line.product_id.isi_perdus) * line.product_id.weight
            else:
                 line.total_weight_dos = 0.0
