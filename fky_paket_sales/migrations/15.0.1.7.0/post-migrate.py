# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Drop the replaced Refresh-All submenu + server action.

    They were superseded by a list-header button next to Create
    (``static/src/js/paket_list_buttons.js`` calling
    ``fky.paket.sales.refresh_all_progress``). Odoo never deletes data
    records that disappear from XML, so remove the stale rows (and their
    ``ir_model_data`` entries) explicitly. Uninstall remains clean: the
    module's ``uninstall_hook`` already covers the remaining menus.
    """
    cr.execute("""
        DELETE FROM ir_ui_menu WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'fky_paket_sales'
              AND model = 'ir.ui.menu'
              AND name = 'menu_refresh_all_progress')
    """)
    cr.execute("""
        DELETE FROM ir_act_server WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'fky_paket_sales'
              AND model = 'ir.actions.server'
              AND name = 'action_refresh_all_progress')
    """)
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'fky_paket_sales'
          AND name IN ('menu_refresh_all_progress',
                       'action_refresh_all_progress')
    """)
