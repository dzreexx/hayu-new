# -*- coding: utf-8 -*-

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    special_instruction = fields.Char(string="Special Instruction")

    def _prepare_invoice(self):
        """Override to propagate special_instruction field to invoice"""
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'special_instruction': self.special_instruction,
        })
        return res
