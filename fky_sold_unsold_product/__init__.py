# -*- coding: utf-8 -*-
from . import models
from . import wizard

def uninstall_hook(cr, registry):
    cr.execute("DROP TABLE IF EXISTS sold_unsold_products_report_line CASCADE;")
    cr.execute("DROP TABLE IF EXISTS sold_unsold_products_report CASCADE;")
