# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta


class CleanupSoldUnsoldReports(models.TransientModel):
    _name = 'cleanup.sold.unsold.reports.wizard'
    _description = 'Cleanup Old Sold & Unsold Products Reports'

    months_old = fields.Integer(
        string='Delete Reports Older Than (Months)',
        default=3,
        required=True,
        help='Reports with period end date more than this many months ago will be deleted'
    )

    def action_cleanup(self):
        """Delete old reports"""
        self.ensure_one()

        if self.months_old < 1:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Invalid Input',
                    'message': 'Months must be at least 1',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        cutoff_date = datetime.now() - relativedelta(months=self.months_old)

        old_reports = self.env['sold.unsold.products.report'].search([
            ('date_to', '!=', False),
            ('date_to', '<', cutoff_date.date())
        ])

        count = len(old_reports)

        if count == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Reports to Delete',
                    'message': f'No reports found older than {self.months_old} months',
                    'type': 'info',
                    'sticky': False,
                }
            }

        old_reports.unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cleanup Successful',
                'message': f'Successfully deleted {count} old report(s)',
                'type': 'success',
                'sticky': False,
            }
        }
