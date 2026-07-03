from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    estimated_weight_dos = fields.Float(
        string='Estimated Weight',
        compute='_compute_weight_dos',
        store=True,
    )
    total_weight_dos = fields.Float(
        string='Total Weight',
        compute='_compute_weight_dos',
        store=True,
    )

    @api.depends('move_line_ids.estimated_weight_dos', 'move_line_ids.total_weight_dos')
    def _compute_weight_dos(self):
        for picking in self:
            picking.estimated_weight_dos = sum(picking.move_line_ids.mapped('estimated_weight_dos'))
            picking.total_weight_dos = sum(picking.move_line_ids.mapped('total_weight_dos'))
