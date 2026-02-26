# -*- coding: utf-8 -*-
from . import models

def uninstall_hook(cr, registry):
    cr.execute("ALTER TABLE stock_move_line DROP COLUMN IF EXISTS delivery_note CASCADE;")
