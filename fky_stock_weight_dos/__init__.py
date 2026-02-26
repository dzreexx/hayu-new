from . import models

def uninstall_hook(cr, registry):
    cr.execute("ALTER TABLE stock_move_line DROP COLUMN IF EXISTS estimated_weight_dos CASCADE;")
    cr.execute("ALTER TABLE stock_move_line DROP COLUMN IF EXISTS total_weight_dos CASCADE;")
