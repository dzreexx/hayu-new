from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fky_backorder_count = fields.Integer(
        string='Backorder Count',
        compute='_compute_fky_backorder_info',
    )

    @api.depends('order_line.product_id', 'partner_id')
    def _compute_fky_backorder_info(self):
        for order in self:
            if not order.partner_id or not order.order_line:
                order.fky_backorder_count = 0
                continue
            product_ids = order.order_line.mapped('product_id').ids
            if not product_ids:
                order.fky_backorder_count = 0
                continue
            moves = self.env['stock.move'].search([
                ('picking_id.partner_id', 'child_of', order.partner_id.commercial_partner_id.id),
                ('picking_id.backorder_id', '!=', False),
                ('picking_id.state', 'not in', ('done', 'cancel')),
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('product_id', 'in', product_ids),
            ])

            unique_product_ids = set(moves.mapped('product_id.id'))
            order.fky_backorder_count = len(unique_product_ids)

    def action_fky_view_backorder_details(self):
        """Open wizard popup showing per-product backorder summary."""
        self.ensure_one()
        product_ids = self.order_line.mapped('product_id').ids
        pickings = self.env['stock.picking'].search([
            ('partner_id', 'child_of', self.partner_id.commercial_partner_id.id),
            ('backorder_id', '!=', False),
            ('state', 'not in', ('done', 'cancel')),
            ('picking_type_code', '=', 'outgoing'),
            ('move_ids_without_package.product_id', 'in', product_ids),
        ])

        # Build per-product lines
        lines = []
        seen_products = set()
        for picking in pickings:
            for move in picking.move_ids_without_package.filtered(lambda m: m.product_id.id in product_ids):
                pid = move.product_id.id
                if pid not in seen_products:
                    seen_products.add(pid)

        for pid in seen_products:
            relevant_pickings = pickings.filtered(
                lambda p: any(m.product_id.id == pid for m in p.move_ids_without_package)
            )
            total_qty = sum(
                m.product_uom_qty
                for p in relevant_pickings
                for m in p.move_ids_without_package
                if m.product_id.id == pid
            )
            lines.append((0, 0, {
                'product_id': pid,
                'backorder_qty': total_qty,
                'backorder_count': len(relevant_pickings),
                'picking_ids': [(6, 0, relevant_pickings.ids)],
            }))

        wizard = self.env['fky.backorder.alert.wizard'].create({
            'sale_order_id': self.id,
            'partner_id': self.partner_id.id,
            'line_ids': lines,
        })

        return {
            'name': _('Pending Backorders — %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'fky.backorder.alert.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }
