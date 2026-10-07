{
    'name': 'FKY Paket Sales Target',
    'version': '15.0.1.8.0',
    'category': 'Sales',
    'summary': 'Track committed sales packages against invoiced quantity',
    'description': """
        This module allows linking a customer group, target quantity and internal categories 
        across a date range to track invoiced product quantities.
    """,
    'author': 'Fukuy',
    'depends': ['base', 'sale', 'account', 'aos_cashback'],
    'data': [
        'security/ir.model.access.csv',
        'views/paket_sales_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fky_paket_sales/static/src/js/paket_list_buttons.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'uninstall_hook': 'uninstall_hook',
}
