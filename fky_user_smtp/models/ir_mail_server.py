from odoo import api, fields, models


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    user_id = fields.Many2one(
        'res.users',
        string='Bound User',
        ondelete='set null',
        index=True,
        help="If set, this outgoing mail server will be used exclusively "
             "when this user sends emails. Leave empty to keep the server "
             "available for all users (default Odoo behavior).",
    )

    def _find_mail_server(self, email_from, mail_servers=None):
        """Override to prioritize user-bound SMTP servers.

        Step 0 (new): If the current user has a dedicated SMTP server,
        return it immediately — skip all from_filter/sequence matching.

        If no user-bound server is found, fall through to the standard
        Odoo selection logic unchanged.
        """
        if mail_servers is None:
            mail_servers = self.sudo().search([], order='sequence')

        # Step 0: Check for a server bound to the current user
        user_server = mail_servers.filtered(
            lambda m: m.user_id.id == self.env.uid
        )
        if user_server:
            return user_server[0], email_from

        # Exclude user-bound servers from the general pool so they
        # don't accidentally match other users via from_filter
        general_servers = mail_servers.filtered(lambda m: not m.user_id)

        return super()._find_mail_server(
            email_from, mail_servers=general_servers
        )
