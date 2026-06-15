from odoo import api, fields, models, _

class FkyBackorderAlertLine(models.TransientModel):
    _name = 'fky.backorder.alert.line'
    _description = 'Backorder Alert Line'

    wizard_id = fields.Many2one('fky.backorder.alert.wizard', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    backorder_qty = fields.Float(string='Qty in Backorder', readonly=True)
    backorder_count = fields.Integer(string='# Backorders', readonly=True)
    picking_ids = fields.Many2many('stock.picking', string='Backorder Transfers', readonly=True)


class FkyBackorderAlertWizard(models.TransientModel):
    _name = 'fky.backorder.alert.wizard'
    _description = 'Backorder Alert Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    line_ids = fields.One2many('fky.backorder.alert.line', 'wizard_id', string='Backorder Lines', readonly=True)

    def action_view_transfers(self):
        """Open all related backorder transfers."""
        picking_ids = self.line_ids.mapped('picking_ids').ids
        return {
            'name': _('Backorder Transfers'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', picking_ids)],
            'target': 'current',
            'context': dict(self.env.context, create=False, edit=False, delete=False),
        }
