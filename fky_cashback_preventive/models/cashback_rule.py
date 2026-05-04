# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime

class CashbackRulePreventive(models.Model):
    _inherit = 'cashback.rule'

    # Fields untuk tracking generation status
    quarter_generated = fields.Boolean(string='Quarter Generated', default=False, track_visibility='onchange')
    quarter_generation_date = fields.Datetime(string='Quarter Generation Date', track_visibility='onchange')
    quarter_generation_year = fields.Integer(string='Quarter Generation Year', track_visibility='onchange')
    quarter_generation_quarter = fields.Selection([
        ('q1', 'Quarter 1'),
        ('q2', 'Quarter 2'), 
        ('q3', 'Quarter 3'),
        ('q4', 'Quarter 4')
    ], string='Quarter Generated', track_visibility='onchange')
    
    # Fields untuk tracking monthly generation status
    month_generated = fields.Boolean(string='Month Generated', default=False, track_visibility='onchange')
    month_generation_date = fields.Datetime(string='Month Generation Date', track_visibility='onchange')
    month_generation_year = fields.Integer(string='Month Generation Year', track_visibility='onchange')
    month_generation_month = fields.Integer(string='Month Generated', track_visibility='onchange')
    
    is_quarter_locked = fields.Boolean(compute='_compute_is_locked')
    is_month_locked = fields.Boolean(compute='_compute_is_locked')

    @api.depends('quarter_generated', 'quarter_generation_year', 'quarter_generation_quarter', 
                 'month_generated', 'month_generation_year', 'month_generation_month')
    def _compute_is_locked(self):
        today = datetime.today()
        for record in self:
            # Check Quarter
            start_month, end_month, current_quarter = record.get_quarter_month(today.month)
            if record.quarter_generated and record.quarter_generation_year == today.year and record.quarter_generation_quarter == current_quarter:
                record.is_quarter_locked = True
            else:
                record.is_quarter_locked = False
                
            # Check Month
            if record.month_generated and record.month_generation_year == today.year and record.month_generation_month == today.month:
                record.is_month_locked = True
            else:
                record.is_month_locked = False

    def reset_quarter_generation(self):
        """Reset quarter generation tracking - hanya untuk admin"""
        self.write({
            'quarter_generated': False,
            'quarter_generation_date': False,
            'quarter_generation_year': False,
            'quarter_generation_quarter': False
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    def reset_month_generation(self):
        """Reset month generation tracking - hanya untuk admin"""
        self.write({
            'month_generated': False,
            'month_generation_date': False,
            'month_generation_year': False,
            'month_generation_month': False
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def compute_quarter_cashback(self):
        for record in self:
            today = datetime.today()
            # Cek apakah sudah pernah generate untuk quarter ini
            start_month, end_month, current_quarter = record.get_quarter_month(today.month)
            
            # Jika sudah pernah generate untuk quarter dan tahun yang sama, maka tidak bisa generate lagi
            if (record.quarter_generated and 
                record.quarter_generation_year == today.year and 
                record.quarter_generation_quarter == current_quarter):
                raise UserError(_("Quarterly cashback untuk %s tahun %s sudah pernah di-generate pada %s. Tidak bisa generate lagi!") % (
                    record.quarter_generation_quarter.upper(), 
                    record.quarter_generation_year,
                    record.quarter_generation_date.strftime('%d/%m/%Y %H:%M:%S') if record.quarter_generation_date else 'tanggal tidak diketahui'
                ))
        
        res = super(CashbackRulePreventive, self).compute_quarter_cashback()

        for record in self:
            today = datetime.today()
            start_month, end_month, current_quarter = record.get_quarter_month(today.month)
            # Update tracking fields setelah berhasil generate
            record.write({
                'quarter_generated': True,
                'quarter_generation_date': fields.Datetime.now(),
                'quarter_generation_year': today.year,
                'quarter_generation_quarter': current_quarter
            })
        return res

    def compute_month_cashback(self):
        for record in self:
            today = datetime.today()
            
            # Cek apakah sudah pernah generate untuk bulan ini
            if (record.month_generated and 
                record.month_generation_year == today.year and 
                record.month_generation_month == today.month):
                raise UserError(_("Monthly cashback untuk bulan %s tahun %s sudah pernah di-generate pada %s. Tidak bisa generate lagi!") % (
                    today.month, 
                    today.year,
                    record.month_generation_date.strftime('%d/%m/%Y %H:%M:%S') if record.month_generation_date else 'tanggal tidak diketahui'
                ))
            
        res = super(CashbackRulePreventive, self).compute_month_cashback()

        for record in self:
            today = datetime.today()
            # Update tracking fields setelah berhasil generate
            record.write({
                'month_generated': True,
                'month_generation_date': fields.Datetime.now(),
                'month_generation_year': today.year,
                'month_generation_month': today.month
            })
        return res
