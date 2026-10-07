# -*- coding: utf-8 -*-


def uninstall_hook(cr, registry):
    """Delete the module's menu tree on uninstall.

    Odoo's own `_module_data_uninstall` refuses to delete a menu whose
    children are also scheduled for deletion (restricted FK), so without
    this the whole menu subtree (Paket Sales container + Target +
    Templates) would be left behind as orphans pointing at deleted
    actions. Uses raw SQL: other modules (e.g.
    simplify_access_management) override ``ir.ui.menu.search`` and
    require an HTTP request, which does not exist during a module
    (un)install.
    """
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = 'fky_paket_sales' AND model = 'ir.ui.menu'")
    menu_ids = [row[0] for row in cr.fetchall()]
    if menu_ids:
        cr.execute(
            "DELETE FROM ir_ui_menu "
            "WHERE id IN %s AND parent_id IN %s",
            (tuple(menu_ids), tuple(menu_ids)))
        cr.execute(
            "DELETE FROM ir_ui_menu WHERE id IN %s",
            (tuple(menu_ids),))
        cr.execute(
            "DELETE FROM ir_model_data "
            "WHERE module = 'fky_paket_sales' AND model = 'ir.ui.menu'")
