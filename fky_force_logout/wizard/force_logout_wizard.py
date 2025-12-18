import uuid
from odoo import models, fields, api

class ForceLogoutWizard(models.TransientModel):
    _name = 'force.logout.wizard'
    _description = 'Force Logout All Users Wizard'

    def action_logout(self):
        # Generate new token to invalidate all specific sessions
        new_token = str(uuid.uuid4())
        self.env['ir.config_parameter'].sudo().set_param('fky_force_logout.token', new_token)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Forced logout initiated. All users (including you) will be logged out on their next request.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
