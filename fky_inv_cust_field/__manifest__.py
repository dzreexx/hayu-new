# -*- coding: utf-8 -*-
{
    "name": "Fky Inv Cust Field",
    "summary": """
        Add Special Instruction field from quotation to invoice""",
    "description": """
         Module for adding Special Instruction field that persists from quotation through order to invoice
    """,
    "author": "FKY",
    "category": "sales",
    "version": "15.0.0.1.0",

    'depends': ['sale', 'account'],

    'data': [
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": False,
}