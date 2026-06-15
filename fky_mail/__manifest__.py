{
    'name': 'Fky Mail',
    'version': '16.0.1.0.0',
    'summary': 'Send mass email with merged PDF attachments for Invoices',
    'category': 'Accounting',
    'author': 'Zaky',
    'depends': ['account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/action_server.xml',
        'views/mail_template_views.xml',
        'data/mail_template_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
