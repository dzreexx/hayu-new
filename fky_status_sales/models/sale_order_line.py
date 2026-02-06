from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # On-hand quantity in the order warehouse stock location
    on_hand_qty = fields.Integer(
        string='On-Hand Qty',
        compute='_compute_quantities',
        store=False,
        help='Physical quantity on hand in the order warehouse stock location'
    )
    
    # Available quantity: physical stock in location not reserved for other orders
    available_qty = fields.Integer(
        string='Available Qty',
        compute='_compute_quantities',
        store=False,
        help='Physical quantity available in warehouse (not reserved for other orders)'
    )
    
    # Status field for visual indicator: 'available' (green) or 'unavailable' (red)
    availability_status = fields.Selection([
        ('available', 'Available'),
        ('unavailable', 'Unavailable')
    ], compute='_compute_availability_status', store=False)
    

    
    @api.depends('product_id', 'order_id.warehouse_id', 'product_uom_qty')
    def _compute_quantities(self):
        """Compute on-hand and available quantities at the order warehouse stock location"""
        for line in self:
            line.on_hand_qty = 0.0
            line.available_qty = 0.0
            
            if not line.product_id:
                continue
            
            # Use order warehouse stock location
            target_location = (line.order_id.warehouse_id and line.order_id.warehouse_id.lot_stock_id)
            if not target_location:
                continue
            
            # Get all quants for this product under the target location (including children)
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', 'child_of', target_location.id)
            ])
            
            # On-hand: sum of physical quantities in quants
            line.on_hand_qty = sum(quants.mapped('quantity'))
            
            # Available base: sum of available_quantity (quantity not reserved in warehouse)
            total_available = sum(quants.mapped('available_quantity'))

            # If order is already confirmed, do NOT subtract this order's lines again
            # because reservations are already reflected in available_quantity.
            is_confirmed = line.order_id.state in ('sale', 'done')
            if is_confirmed:
                line.available_qty = max(total_available, -999)
                continue

            # Draft/sent quotation: show preview by subtracting saved lines and the current unsaved line
            saved_lines = line.order_id.order_line.filtered(lambda l: l.product_id == line.product_id and l.id)
            saved_qty = sum(saved_lines.mapped('product_uom_qty'))
            current_line_qty = line.product_uom_qty if not line.id else 0

            line.available_qty = max(total_available - saved_qty - current_line_qty, -999)
    
    @api.depends('product_id', 'order_id.warehouse_id', 'product_uom_qty')
    def _compute_availability_status(self):
        """Status rule: if baseline warehouse available is 0, mark unavailable.
        Otherwise available if (current qty - original available before current) <= 0.
        Original available = warehouse available for product minus other saved lines in this order (excluding current).
        """
        for line in self:
            # Default
            line.availability_status = 'unavailable'
            
            if not line.product_id:
                continue
            
            target_location = (line.order_id.warehouse_id and line.order_id.warehouse_id.lot_stock_id)
            if not target_location:
                continue
            
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', 'child_of', target_location.id)
            ])
            total_available = sum(quants.mapped('available_quantity'))
            
            # New rule: zero baseline availability => unavailable
            if total_available <= 0:
                line.availability_status = 'unavailable'
                continue
            
            # Other saved lines for the same product (exclude current if saved)
            other_saved_lines = line.order_id.order_line.filtered(
                lambda l: l.product_id == line.product_id and l.id and l.id != line.id
            )
            other_saved_qty = sum(other_saved_lines.mapped('product_uom_qty'))
            
            original_available_before_current = total_available - other_saved_qty
            shortage = line.product_uom_qty - original_available_before_current
            
            line.availability_status = 'available' if shortage <= 0 else 'unavailable'
    
    # Manual onchanges are not needed: compute fields above already depend
    # on product, warehouse, and quantity; Odoo will recompute automatically.
