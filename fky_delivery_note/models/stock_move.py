# -*- coding: utf-8 -*-

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        """Override to propagate delivery_note from origin move lines to new move lines.
        This ensures notes carry over in multi-step transfers (e.g. Toko → Transit → Gudang).
        """
        res = super(StockMove, self)._action_assign()
        moves_with_orig = self.filtered(lambda m: m.move_orig_ids)
        if moves_with_orig:
            for move in moves_with_orig:
                # Group origin lines by product_id and (optionally) lot_id
                origin_lines = move.move_orig_ids.mapped('move_line_ids').filtered(lambda l: l.delivery_note)
                if not origin_lines:
                    continue
                
                # Pre-map them for fast lookup
                note_map = {}
                for l in origin_lines:
                    key = (l.product_id.id, l.lot_id.id if l.lot_id else False)
                    if key not in note_map:
                        note_map[key] = l.delivery_note
                
                # Apply to current move lines
                for move_line in move.move_line_ids:
                    if not move_line.delivery_note:
                        key = (move_line.product_id.id, move_line.lot_id.id if move_line.lot_id else False)
                        # Fallback to product-only match if full key doesn't match
                        fallback_key = (move_line.product_id.id, False)
                        
                        if key in note_map:
                            move_line.delivery_note = note_map[key]
                        elif fallback_key in note_map:
                            move_line.delivery_note = note_map[fallback_key]
        return res
