from odoo import api, fields, models


class StockAlert(models.Model):
    _name = 'stock.alert.rule'
    _description = 'Stock Alert Rule'
    _rec_name = 'product_id'
    _order = 'is_favorite desc, qty_available asc'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        domain=[('complete_name', 'in', ['TKADR/Stock', 'GDADR/Stock'])],
    )

    min_qty = fields.Float(
        string='Minimum Qty',
        required=True,
        default=1,
    )

    is_favorite = fields.Boolean(
        string='Favorite',
    )

    qty_available = fields.Float(
        string='Current Qty',
        compute='_compute_qty',
        store=True,
    )

    state = fields.Selection([
        ('ok', 'OK'),
        ('low', 'Low Stock'),
    ], string='Status', compute='_compute_qty', store=True)

    _sql_constraints = [
        ('product_location_uniq',
         'unique(product_id, location_id)',
         'An alert rule already exists for this product and location!'),
    ]

    @api.depends('product_id', 'location_id', 'min_qty')
    def _compute_qty(self):
        Quant = self.env['stock.quant'].sudo()
        for rec in self:
            qty = 0.0
            # Retrieve database IDs (resolves NewId objects during virtual/dry-run checks)
            prod_id = rec.product_id._origin.id if hasattr(rec.product_id, '_origin') else rec.product_id.id
            loc_id = rec.location_id._origin.id if hasattr(rec.location_id, '_origin') else rec.location_id.id
            
            if isinstance(prod_id, int) and isinstance(loc_id, int):
                quants = Quant.search([
                    ('product_id', '=', prod_id),
                    ('location_id', '=', loc_id),
                ])
                qty = sum(quants.mapped('quantity'))
            rec.qty_available = qty
            rec.state = 'low' if qty < rec.min_qty else 'ok'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Force immediate DB save to prevent cache issues during import
        for rec in records:
            rec._compute_qty()
            rec.sudo().write({
                'qty_available': rec.qty_available,
                'state': rec.state
            })
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ['product_id', 'location_id', 'min_qty']):
            for rec in self:
                rec._compute_qty()
                rec.sudo().write({
                    'qty_available': rec.qty_available,
                    'state': rec.state
                })
        return res
