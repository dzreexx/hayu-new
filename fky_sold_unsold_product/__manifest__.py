# -*- coding: utf-8 -*-
{
    'name': 'FKY Sold & Unsold Products Report',
    'version': '15.0.1.0.0',
    'category': 'Sales',
    'summary': 'Report showing sold and unsold products in a specific period',
    'description': """
Sold & Unsold Products Report
==============================
This module provides a report to identify products that have been sold
AND products that have NOT been sold during a specific period.

Features:
---------
* Filter by month and year or custom date range
* Shows sold products with quantities and revenue
* Shows unsold products with zero sales in the selected period
* Displays product details: name, category, stock quantity
* Shows last sale date and price
* Excludes archived products
* Accessible via Sales > Reporting > Sold & Unsold Products
    """,
    'author': 'FKY',
    'website': '',
    'depends': ['sale', 'product', 'stock', 'aos_product_adireksa', 'aos_notify_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cleanup_old_reports_views.xml',
        'views/sold_unsold_report_views.xml',
    ],
    'installable': True,
    'uninstall_hook': 'uninstall_hook',
    'application': False,
    'auto_install': False,
}
