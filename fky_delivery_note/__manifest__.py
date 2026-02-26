# -*- coding: utf-8 -*-
{
    "name": "FKY Stock Move Line Note",
    "summary": """Add note field to stock move lines in all picking types""",
    "description": """
        Module for adding notes to stock move lines in detailed operations.
        Works with delivery orders, receipts, and internal transfers.
    """,
    "author": "FKY",
    "website": "",
    "category": "stock",
    "version": "15.0.0.1.0",

    'depends': ['stock', 'stock_barcode'],

    'data': [
        'views/stock_move_line_views.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'fky_delivery_note/static/src/components/line.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'uninstall_hook': 'uninstall_hook',
    "auto_install": False,
    "application": False,
}
