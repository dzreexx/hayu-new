# -*- coding: utf-8 -*-
{
    "name": "AOS Delivery Order Note",
    "summary": """
        Add note field to delivery order product lines""",
    "description": """
         Module for adding notes to delivery order product lines in detailed operations
    """,
    "author": "Alphasoft",
    "website": "https://www.alphasoft.co.id/",
    "category": "stock",
    "version": "15.0.0.1.0",

    'depends': ['stock', 'stock_barcode'],

    'data': [
        'views/stock_move_line_views.xml',
        ],
    'assets': {
        'web.assets_qweb': [
            'aos_delivery_note/static/src/components/line.xml',
        ],
    },
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
