# -*- coding: utf-8 -*-

from odoo import models, fields

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    delivery_note = fields.Text(string="Note")

    def _get_fields_stock_barcode(self):
        """ Add delivery_note to the fields available in barcode interface """
        fields = super(StockMoveLine, self)._get_fields_stock_barcode()
        fields.append('delivery_note')
        return fields

