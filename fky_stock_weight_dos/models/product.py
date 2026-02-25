from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # We use the default 'weight' field from Odoo
    # No additional fields needed
