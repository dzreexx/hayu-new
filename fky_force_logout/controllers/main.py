from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Home, Session

class ForceLogoutHome(Home):
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        response = super(ForceLogoutHome, self).web_login(redirect=redirect, **kw)
        if request.session.uid:
            token = request.env['ir.config_parameter'].sudo().get_param('fky_force_logout.token')
            if token:
                request.session['fky_logout_token'] = token
        return response

class ForceLogoutSession(Session):
    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        res = super(ForceLogoutSession, self).authenticate(db, login, password, base_location)
        if request.session.uid:
            token = request.env['ir.config_parameter'].sudo().get_param('fky_force_logout.token')
            if token:
                request.session['fky_logout_token'] = token
        return res
