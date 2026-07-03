# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FkyPaketSalesTemplate(models.Model):
    _name = 'fky.paket.sales.template'
    _description = 'Paket Sales Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    internal_category_ids = fields.Many2many(
        'internal.category', string='Internal Categories', required=True)
    target_qty = fields.Integer(string='Target (Pcs)', required=True, default=0)
