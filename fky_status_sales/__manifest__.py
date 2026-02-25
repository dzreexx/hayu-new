{
    'name': 'FKY Status Sales',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Show stock information in quotations',
    'description': """
    This module adds stock information to quotation lines:
    1. On-hand quantity (total stock across all locations)
    2. Available quantity (specific to quotation's warehouse)
    """,
    'depends': ['sale', 'stock'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}