{
    'name': 'User SMTP Binding',
    'version': '15.0.1.0.0',
    'summary': 'Bind outgoing SMTP mail servers to specific users',
    'description': """
        This module allows you to assign an outgoing mail server (SMTP)
        to a specific user. When that user sends an email, the system
        will automatically use their assigned SMTP server instead of
        the default from_filter/sequence-based selection.

        If a user has no assigned SMTP server, the standard Odoo
        selection logic applies as fallback.

        Safe to uninstall — Odoo will automatically clean up the added
        field and restore default behavior.
    """,
    'category': 'Technical',
    'author': 'FKY',
    'depends': ['base', 'mail'],
    'data': [
        'views/ir_mail_server_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
