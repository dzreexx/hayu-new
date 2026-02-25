# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    internal_category = fields.Many2one(
        'internal.category', 
        string='Internal Category',
        related='product_tmpl_id.internal_category',
        store=True,
        readonly=True
    )
