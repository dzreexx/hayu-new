# -*- coding: utf-8 -*-

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        """Override to propagate delivery_note from origin move lines to new move lines.
        This ensures notes carry over in multi-step transfers (e.g. Toko → Transit → Gudang).
        """
        res = super(StockMove, self)._action_assign()
        for move in self:
            if move.move_orig_ids:
                # Collect notes from origin move lines grouped by product
                origin_lines = move.move_orig_ids.mapped('move_line_ids').filtered(
                    lambda l: l.delivery_note
                )
                if origin_lines:
                    for move_line in move.move_line_ids:
                        if not move_line.delivery_note:
                            # Find matching origin line by product (and lot if applicable)
                            matching = origin_lines.filtered(
                                lambda l: l.product_id == move_line.product_id
                            )
                            if move_line.lot_id:
                                lot_match = matching.filtered(
                                    lambda l: l.lot_id == move_line.lot_id
                                )
                                if lot_match:
                                    matching = lot_match
                            if matching:
                                move_line.delivery_note = matching[0].delivery_note
        return res
