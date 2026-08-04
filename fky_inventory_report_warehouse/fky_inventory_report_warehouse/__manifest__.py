{
    'name': 'FKY Inventory Report Warehouse',
    'version': '15.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Filter historical inventory by warehouse',
    'author': 'FKY',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'data': [
        'views/stock_quantity_history_views.xml',
    ],
    'installable': True,
    'application': False,
}
