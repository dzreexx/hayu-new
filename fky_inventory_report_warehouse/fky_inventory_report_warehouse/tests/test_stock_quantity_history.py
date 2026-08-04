"""Tests for warehouse-scoped historical inventory actions."""

from odoo.tests.common import TransactionCase


class TestStockQuantityHistory(TransactionCase):
    """Ensure the selected warehouse is retained in the stock context."""

    def test_warehouse_is_added_to_history_action(self):
        """Odoo's at-date action receives both date and warehouse contexts."""
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not warehouse:
            self.skipTest('No warehouse is available for this company.')
        wizard = self.env['stock.quantity.history'].create({
            'warehouse_id': warehouse.id,
        })
        action = wizard.open_at_date()
        self.assertEqual(action['context']['warehouse'], warehouse.id)
