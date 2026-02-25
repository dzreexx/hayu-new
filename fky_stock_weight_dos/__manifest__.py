
{
    'name': 'Stock Weight Per Dos',
    'version': '15.0.0.1',
    'summary': 'Add Weight Per Dos field and calculate total weight based on isi perdus',
    'author': 'FKY',
    'category': 'Stock',
    'depends': ['stock', 'product', 'aos_base_product'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
}
