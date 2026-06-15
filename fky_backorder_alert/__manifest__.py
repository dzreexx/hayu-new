{
    'name': 'Backorder Alert',
    'version': '15.0.1.0.0',
    'category': 'Sales',
    'summary': 'Smart button alert when a customer already has products in backorder.',
    'description': """
        Adds a smart button on Quotations/Sales Orders showing the number of pending
        backorders for the customer. Click it to see a clear per-product summary table
        with quantities and number of backorder transfers.
    """,
    'author': 'Fukuy',
    'depends': ['sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
