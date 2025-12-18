from odoo import models
from odoo.http import request
from odoo.exceptions import AccessDenied

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        res = super(IrHttp, cls)._authenticate(endpoint)
        if request.session.uid:
            # Check global logout token
            current_token = request.env['ir.config_parameter'].sudo().get_param('fky_force_logout.token')
            if current_token:
                session_token = request.session.get('fky_logout_token')
                if session_token != current_token:
                    request.session.logout()
                    raise AccessDenied("Session expired due to forced global logout.")
        return res
