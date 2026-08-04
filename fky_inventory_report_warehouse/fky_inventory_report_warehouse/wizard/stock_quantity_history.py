"""Add warehouse scope to Odoo's historical inventory wizard."""

from odoo import fields, models
from odoo.exceptions import ValidationError


class StockQuantityHistory(models.TransientModel):
    """Pass the selected warehouse into the standard at-date stock action."""

    _inherit = 'stock.quantity.history'

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        check_company=True,
        domain="[('company_id', 'in', allowed_company_ids)]",
    )

    def open_at_date(self):
        """Open standard historical quantities scoped to the selected warehouse."""
        self.ensure_one()
        if self.warehouse_id and self.warehouse_id.company_id not in self.env.companies:
            raise ValidationError('You are not allowed to view this warehouse.')
        action = super().open_at_date()
        if self.warehouse_id:
            action['context'] = dict(action.get('context', {}), warehouse=self.warehouse_id.id)
        return action
