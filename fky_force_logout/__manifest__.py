{
    'name': 'FKY Force Logout All Users',
    'version': '1.0',
    'summary': 'Add a button in settings to logout all users.',
    'description': """
        This module adds a button in General Settings to force logout all users.
        When clicked, it updates a system parameter that invalidates all existing sessions.
    """,
    'category': 'Tools',
    'author': 'Zulfikar',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/force_logout_wizard_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}
