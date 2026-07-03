# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class FkyPaketSales(models.Model):
    _name = 'fky.paket.sales'
    _description = 'Paket Sales Target Tracking'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name/Reference', required=True, tracking=True)
    customer_group_id = fields.Many2one('adireksa.customer.target', string='Customer Group', required=True, tracking=True)
    line_ids = fields.One2many('fky.paket.sales.line', 'paket_id', string='Commitment Lines')
    
    date_start = fields.Date(string='Start Date', required=True, tracking=True)
    date_end = fields.Date(string='End Date', required=True, tracking=True)
    
    target_qty = fields.Integer(string='Total Target', compute='_compute_totals', store=True)
    current_qty_so = fields.Integer(string='Total SO', compute='_compute_totals', store=True)
    current_qty_inv = fields.Integer(string='Total Invoiced', compute='_compute_totals', store=True)
    progress_so = fields.Integer(string='Overall SO Progress (%)', compute='_compute_totals', store=True)
    progress_inv = fields.Integer(string='Overall Inv Progress (%)', compute='_compute_totals', store=True)
    progress_so_html = fields.Html(string='Overall SO Progress', compute='_compute_progress_html')
    progress_inv_html = fields.Html(string='Overall Inv Progress', compute='_compute_progress_html')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('partially_done', 'Partially Done'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    template_ids = fields.Many2many(
        'fky.paket.sales.template', string='Apply Templates')

    @api.onchange('template_ids')
    def _onchange_template_ids(self):
        if self.template_ids:
            lines = [(5, 0, 0)]
            for tmpl in self.template_ids:
                for cat in tmpl.internal_category_ids:
                    lines.append((0, 0, {
                        'internal_category_id': cat.id,
                        'target_qty': tmpl.target_qty,
                    }))
            self.line_ids = lines

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('template_ids') and vals.get('template_ids')[0][2] and not vals.get('line_ids'):
                tmpl_ids = vals['template_ids'][0][2]
                templates = self.env['fky.paket.sales.template'].browse(tmpl_ids)
                line_vals = []
                for tmpl in templates:
                    for cat in tmpl.internal_category_ids:
                        line_vals.append((0, 0, {
                            'internal_category_id': cat.id,
                            'target_qty': tmpl.target_qty,
                        }))
                if line_vals:
                    vals['line_ids'] = line_vals
        return super().create(vals_list)

    @api.depends('line_ids.target_qty', 'line_ids.current_qty_so', 'line_ids.current_qty_inv')
    def _compute_totals(self):
        for record in self:
            total_target = sum(record.line_ids.mapped('target_qty'))
            total_so = sum(record.line_ids.mapped('current_qty_so'))
            total_inv = sum(record.line_ids.mapped('current_qty_inv'))
            record.target_qty = int(total_target)
            record.current_qty_so = int(total_so)
            record.current_qty_inv = int(total_inv)
            if total_target > 0:
                record.progress_so = int(min((total_so / total_target) * 100, 100))
                record.progress_inv = int(min((total_inv / total_target) * 100, 100))
            else:
                record.progress_so = 0
                record.progress_inv = 0

    @api.depends('progress_so', 'progress_inv', 'date_end', 'state')
    def _compute_progress_html(self):
        for record in self:
            def get_html(progress, current_qty):
                color = '#6c757d'
                bg_color = '#e9ecef'
                width = min(progress, 100) if progress > 0 else 0
                
                if progress >= 100:
                    color = '#007bff'
                    width = 100
                else:
                    today = fields.Date.context_today(record)
                    is_expired = record.date_end and today > record.date_end
                    is_closed = record.state in ('done', 'partially_done')
                    if is_expired or is_closed:
                        color = '#dc3545'
                        bg_color = '#f5c6cb'
                
                display_width = width if width > 0 else 0.5
                
                return f"""
                <div style="width: 100%; background-color: {bg_color}; border-radius: 5px; overflow: hidden; height: 26px; border: 1px solid #ccc; position: relative;">
                    <div style="width: {display_width}%; background-color: {color}; height: 100%; display: flex; align-items: center; justify-content: center; transition: width 0.5s;">
                    </div>
                    <div style="position: absolute; width: 100%; height: 100%; top: 0; left: 0; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px; color: {'white' if width > 50 or bg_color == '#dc3545' else 'black'};">
                        {int(progress)}% ({int(current_qty)} / {int(record.target_qty)})
                    </div>
                </div>
                """
            
            record.progress_so_html = get_html(record.progress_so, record.current_qty_so)
            record.progress_inv_html = get_html(record.progress_inv, record.current_qty_inv)

    def action_running(self):
        self.write({'state': 'running'})
        self._compute_progress()

    def action_done(self):
        self._compute_progress()
        for record in self:
            all_achieved = True
            for line in record.line_ids:
                if line.progress_inv < 100:
                    all_achieved = False
                    break
            if all_achieved:
                record.write({'state': 'done'})
            else:
                record.write({'state': 'partially_done'})

    def _compute_progress(self):
        self.line_ids._compute_current_qty()
        self._compute_totals()
        self._compute_progress_html()
        self.line_ids._compute_progress_html()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})


class FkyPaketSalesLine(models.Model):
    _name = 'fky.paket.sales.line'
    _description = 'Paket Sales Commitment Line'

    paket_id = fields.Many2one('fky.paket.sales', string='Paket Sales Reference', required=True, ondelete='cascade')
    internal_category_id = fields.Many2one('internal.category', string='Internal Category', required=True)
    
    target_qty = fields.Integer(string='Target (Pcs)', required=True, default=0)
    current_qty_so = fields.Integer(string='SO Qty', compute='_compute_current_qty')
    current_qty_inv = fields.Integer(string='Invoiced Qty', compute='_compute_current_qty')
    progress_so = fields.Integer(string='SO Progress (%)', compute='_compute_current_qty')
    progress_inv = fields.Integer(string='Inv Progress (%)', compute='_compute_current_qty')
    progress_so_html = fields.Html(string='SO Progress', compute='_compute_progress_html')
    progress_inv_html = fields.Html(string='Inv Progress', compute='_compute_progress_html')

    @api.depends('paket_id.customer_group_id', 'internal_category_id', 'paket_id.date_start', 'paket_id.date_end', 'paket_id.state')
    def _compute_current_qty(self):
        for record in self:
            if record.paket_id.state in ('draft', 'cancel') or not record.paket_id.customer_group_id or not record.paket_id.date_start or not record.paket_id.date_end or not record.internal_category_id:
                record.current_qty_so = 0
                record.current_qty_inv = 0
                record.progress_so = 0
                record.progress_inv = 0
                continue
            
            domain_category = [
                '|',
                ('internal_category', '=', record.internal_category_id.id),
                ('product_id.internal_category', '=', record.internal_category_id.id)
            ]
            
            # SO calculation
            domain_so = [
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', record.paket_id.date_start),
                ('order_id.date_order', '<=', record.paket_id.date_end),
                ('display_type', '=', False)
            ]
            domain_group_so = [
                '|', '|',
                ('order_id.partner_id.group_id', '=', record.paket_id.customer_group_id.id),
                ('order_id.partner_id.commercial_partner_id.group_id', '=', record.paket_id.customer_group_id.id),
                ('order_id.partner_id.group_id.name', '=', record.paket_id.customer_group_id.name)
            ]
            final_domain_so = domain_so + domain_group_so + domain_category
            lines_so = self.env['sale.order.line'].search(final_domain_so)
            total_so = sum(lines_so.mapped('product_uom_qty'))
            
            # Invoice calculation
            domain_invoice = [
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state', '=', 'posted'),
                ('move_id.invoice_date', '>=', record.paket_id.date_start),
                ('move_id.invoice_date', '<=', record.paket_id.date_end),
                ('exclude_from_invoice_tab', '=', False)
            ]
            domain_group_inv = [
                '|', '|',
                ('move_id.partner_id.group_id', '=', record.paket_id.customer_group_id.id),
                ('move_id.partner_id.commercial_partner_id.group_id', '=', record.paket_id.customer_group_id.id),
                ('move_id.partner_id.group_id.name', '=', record.paket_id.customer_group_id.name)
            ]
            final_domain_inv = domain_invoice + domain_group_inv + domain_category
            lines_inv = self.env['account.move.line'].search(final_domain_inv)
            total_inv = sum(lines_inv.mapped('quantity'))
            
            record.current_qty_so = int(total_so)
            record.current_qty_inv = int(total_inv)
            if record.target_qty > 0:
                record.progress_so = int(min((total_so / record.target_qty) * 100, 100))
                record.progress_inv = int(min((total_inv / record.target_qty) * 100, 100))
            else:
                record.progress_so = 0
                record.progress_inv = 0

    @api.depends('progress_so', 'progress_inv', 'paket_id.date_end', 'paket_id.state')
    def _compute_progress_html(self):
        for record in self:
            def get_html(progress, current_qty):
                color = '#6c757d'
                bg_color = '#e9ecef'
                width = min(progress, 100) if progress > 0 else 0
                
                if progress >= 100:
                    color = '#007bff'
                    width = 100
                else:
                    today = fields.Date.context_today(record)
                    is_expired = record.paket_id.date_end and today > record.paket_id.date_end
                    is_closed = record.paket_id.state in ('done', 'partially_done')
                    if is_expired or is_closed:
                        color = '#dc3545'
                        bg_color = '#f5c6cb'
                
                display_width = width if width > 0 else 0.5
                
                return f"""
                <div style="width: 100%; background-color: {bg_color}; border-radius: 5px; overflow: hidden; height: 26px; border: 1px solid #ccc; position: relative; min-width: 150px;">
                    <div style="width: {display_width}%; background-color: {color}; height: 100%; display: flex; align-items: center; justify-content: center; transition: width 0.5s;">
                    </div>
                    <div style="position: absolute; width: 100%; height: 100%; top: 0; left: 0; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px; color: {'white' if width > 50 or bg_color == '#dc3545' else 'black'};">
                        {int(progress)}% ({int(current_qty)} / {int(record.target_qty)})
                    </div>
                </div>
                """
                
            record.progress_so_html = get_html(record.progress_so, record.current_qty_so)
            record.progress_inv_html = get_html(record.progress_inv, record.current_qty_inv)
