{
    'name': 'FKY Stock Alert Dashboard',
    'version': '15.0.1.0',
    'category': 'Inventory',
    'summary': 'Simple stock alert based on actual stock per location',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_alert_generator_views.xml',
        'views/stock_alert_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
}
