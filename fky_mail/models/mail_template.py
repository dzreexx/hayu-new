from odoo import models, fields

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    is_mass_pdf_default = fields.Boolean(string="Default for Mass PDF", help="If checked, this template will be selected by default in the Mass PDF Mail wizard.")
