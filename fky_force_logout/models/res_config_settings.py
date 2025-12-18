from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def action_force_logout_all_users(self):
        """ Opens the confirmation wizard for logging out all users. """
        return {
            'name': 'Force Logout All Users',
            'type': 'ir.actions.act_window',
            'res_model': 'force.logout.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
