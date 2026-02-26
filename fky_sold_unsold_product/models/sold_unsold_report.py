# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar


class SoldUnsoldReport(models.Model):
    _name = 'sold.unsold.products.report'
    _description = 'Sold & Unsold Products Report'
    _order = 'year desc, month desc, id desc'

    name = fields.Char(string='Report Name', compute='_compute_name', store=True)
    filter_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('custom', 'Custom Date Range'),
    ], string='Filter Type', required=True, default='monthly')
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', default=str(datetime.now().month))
    year = fields.Integer(string='Year', default=datetime.now().year)
    date_from = fields.Date(string='Date From', compute='_compute_dates', store=True, readonly=False)
    date_to = fields.Date(string='Date To', compute='_compute_dates', store=True, readonly=False)

    report_type = fields.Selection([
        ('both', 'Sold & Unsold'),
        ('sold', 'Sold Only'),
        ('unsold', 'Unsold Only'),
    ], string='Generate', required=True, default='both')
    categ_ids = fields.Many2many('product.category', string='Product Categories',
                                 help='Leave empty to include all categories')
    internal_category_ids = fields.Many2many('internal.category', string='Internal Categories',
                                             help='Leave empty to include all internal categories')
    customer_ids = fields.Many2many('res.partner', string='Customers',
                                    domain="[('customer_rank', '>', 0)]",
                                    help='Leave empty to include all customers')

    unsold_line_ids = fields.One2many('sold.unsold.products.report.line', 'report_id',
                                      string='Unsold Products',
                                      domain=[('line_type', '=', 'unsold')])
    sold_line_ids = fields.One2many('sold.unsold.products.report.line', 'report_id',
                                    string='Sold Products',
                                    domain=[('line_type', '=', 'sold')])

    total_unsold_products = fields.Integer(string='Total Unsold Products',
                                           compute='_compute_totals', store=True)
    total_sold_products = fields.Integer(string='Total Sold Products',
                                         compute='_compute_totals', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
    ], string='Status', default='draft', readonly=True)

    @api.depends('filter_type', 'month', 'year', 'date_from', 'date_to')
    def _compute_name(self):
        for record in self:
            if record.filter_type == 'monthly' and record.month and record.year:
                month_name = dict(record._fields['month'].selection).get(record.month)
                record.name = f"Sales Report - {month_name} {record.year}"
            elif record.filter_type == 'custom' and record.date_from and record.date_to:
                record.name = f"Sales Report - {record.date_from} to {record.date_to}"
            else:
                record.name = "Sales Report"

    @api.depends('filter_type', 'month', 'year')
    def _compute_dates(self):
        for record in self:
            if record.filter_type == 'monthly':
                if record.month and record.year:
                    month_int = int(record.month)
                    record.date_from = datetime(record.year, month_int, 1).date()
                    last_day = calendar.monthrange(record.year, month_int)[1]
                    record.date_to = datetime(record.year, month_int, last_day).date()
                else:
                    record.date_from = False
                    record.date_to = False

    @api.depends('unsold_line_ids', 'sold_line_ids')
    def _compute_totals(self):
        for record in self:
            record.total_unsold_products = len(record.unsold_line_ids)
            record.total_sold_products = len(record.sold_line_ids)

    def action_generate_report(self):
        """Generate the sold & unsold products report for the selected period"""
        self.ensure_one()

        # Clear existing lines
        self.env['sold.unsold.products.report.line'].search([
            ('report_id', '=', self.id)
        ]).unlink()

        if not self.date_from or not self.date_to:
            return

        # Get all sellable, non-archived products
        product_domain = [
            ('sale_ok', '=', True),
            ('active', '=', True),
        ]
        # Filter by selected categories if any
        if self.categ_ids:
            product_domain.append(('categ_id', 'child_of', self.categ_ids.ids))
        if self.internal_category_ids:
            product_domain.append(('internal_category', 'in', self.internal_category_ids.ids))
        all_products = self.env['product.product'].search(product_domain)

        # Get invoice lines in this period (posted customer invoices only)
        invoice_domain = [
            ('move_id.invoice_date', '>=', self.date_from),
            ('move_id.invoice_date', '<=', self.date_to),
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', '=', 'out_invoice'),
            ('exclude_from_invoice_tab', '=', False),
            ('product_id', '!=', False),
        ]
        if self.customer_ids:
            invoice_domain.append(('move_id.partner_id', 'in', self.customer_ids.ids))

        invoice_lines_in_period = self.env['account.move.line'].search(invoice_domain)

        # Get products that WERE sold in this period
        sold_products = invoice_lines_in_period.mapped('product_id')

        # Get ALL sold products (regardless of customer filter) to calculate true unsold
        all_invoice_lines_in_period = self.env['account.move.line'].search([
            ('move_id.invoice_date', '>=', self.date_from),
            ('move_id.invoice_date', '<=', self.date_to),
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', '=', 'out_invoice'),
            ('exclude_from_invoice_tab', '=', False),
            ('product_id', '!=', False),
        ])
        all_sold_products = all_invoice_lines_in_period.mapped('product_id')

        # Get unsold products (products not sold to ANYONE in this period)
        unsold_products = all_products - all_sold_products

        lines_vals = []
        sold_count = 0
        unsold_count = 0

        # --- SOLD PRODUCTS ---
        if self.report_type in ('both', 'sold'):
            # Filter invoice lines to only include products in our category filter
            if self.categ_ids or self.internal_category_ids:
                invoice_lines_in_period = invoice_lines_in_period.filtered(
                    lambda l: l.product_id in all_products
                )
            # Group invoice lines by product to aggregate quantities and amounts
            sold_data = {}
            for line in invoice_lines_in_period:
                pid = line.product_id.id
                if pid not in sold_data:
                    sold_data[pid] = {
                        'product_id': line.product_id,
                        'total_qty': 0.0,
                        'total_amount': 0.0,
                        'order_count': set(),
                        'last_order_date': False,
                        'last_price_unit': 0.0,
                    }
                sold_data[pid]['total_qty'] += line.quantity
                sold_data[pid]['total_amount'] += line.price_subtotal
                sold_data[pid]['order_count'].add(line.move_id.id)
                order_date = line.move_id.invoice_date or line.move_id.date
                if not sold_data[pid]['last_order_date'] or order_date > sold_data[pid]['last_order_date']:
                    sold_data[pid]['last_order_date'] = order_date
                    sold_data[pid]['last_price_unit'] = line.price_unit

            for pid, data in sold_data.items():
                product = data['product_id']
                lines_vals.append({
                    'report_id': self.id,
                    'line_type': 'sold',
                    'product_id': product.id,
                    'sold_qty': data['total_qty'],
                    'sold_amount': data['total_amount'],
                    'order_count': len(data['order_count']),
                    'last_sale_date': data['last_order_date'],
                    'last_sale_price': data['last_price_unit'],
                })
            sold_count = len(sold_data)

        # --- UNSOLD PRODUCTS ---
        if self.report_type in ('both', 'unsold'):
            last_sale_data = {}
            if unsold_products:
                self.env.cr.execute("""
                    SELECT DISTINCT ON (l.product_id)
                        l.product_id,
                        COALESCE(m.invoice_date, m.date) AS last_date,
                        l.price_unit
                    FROM account_move_line l
                    JOIN account_move m ON l.move_id = m.id
                    WHERE l.product_id IN %s
                      AND m.state = 'posted'
                      AND m.move_type = 'out_invoice'
                      AND l.exclude_from_invoice_tab = False
                      AND l.company_id IN %s
                    ORDER BY l.product_id, COALESCE(m.invoice_date, m.date) DESC, l.id DESC
                """, [tuple(unsold_products.ids), tuple(self.env.companies.ids) if hasattr(self.env, 'companies') else tuple([self.env.company.id])])
                
                for row in self.env.cr.fetchall():
                    last_sale_data[row[0]] = {'date': row[1], 'price': row[2]}

            for product in unsold_products:
                data = last_sale_data.get(product.id)
                lines_vals.append({
                    'report_id': self.id,
                    'line_type': 'unsold',
                    'product_id': product.id,
                    'last_sale_date': data['date'] if data else False,
                    'last_sale_price': data['price'] if data else False,
                })
            unsold_count = len(unsold_products)

        # Create all lines at once
        if lines_vals:
            self.env['sold.unsold.products.report.line'].create(lines_vals)

        # Build notification message
        if self.filter_type == 'monthly' and self.month:
            period_label = f"{dict(self._fields['month'].selection).get(self.month)} {self.year}"
        else:
            period_label = f"{self.date_from} to {self.date_to}"

        # Build result message parts
        msg_parts = []
        if self.report_type in ('both', 'sold'):
            msg_parts.append(f'{sold_count} sold')
        if self.report_type in ('both', 'unsold'):
            msg_parts.append(f'{unsold_count} unsold')
        msg = ' and '.join(msg_parts)

        self.write({'state': 'generated'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Report Generated',
                'message': f'Found {msg} products for {period_label}',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_reset_draft(self):
        self.ensure_one()
        self.env['sold.unsold.products.report.line'].search([
            ('report_id', '=', self.id)
        ]).unlink()
        self.write({'state': 'draft'})

    def action_export_excel(self):
        self.ensure_one()
        
        if not self.sold_line_ids and not self.unsold_line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Empty Report',
                    'message': 'No products found to export.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        import io
        import base64
        try:
            import xlsxwriter
        except ImportError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'xlsxwriter is not installed. Please install it to export Excel.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'
        })
        text_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})

        if self.report_type in ('both', 'sold'):
            sheet_sold = workbook.add_worksheet('Sold Products')
            headers_sold = ['Product Name', 'Internal Reference', 'Product Category', 'Internal Category', 'Qty Sold', 'Total Sales Amount', 'No. of Orders', 'Quantity On Hand', 'Sales Price', 'Last Sale Date', 'Last Sale Price']
            for col_num, header in enumerate(headers_sold):
                sheet_sold.write(0, col_num, header, header_format)
            sheet_sold.set_column(0, 0, 30)
            sheet_sold.set_column(1, 10, 15)

            row = 1
            for line in self.sold_line_ids.sorted(lambda l: l.product_name or ''):
                sheet_sold.write(row, 0, line.product_name or '', text_format)
                sheet_sold.write(row, 1, line.default_code or '', text_format)
                sheet_sold.write(row, 2, line.categ_id.display_name or '', text_format)
                sheet_sold.write(row, 3, line.internal_category_id.display_name or '', text_format)
                sheet_sold.write(row, 4, line.sold_qty or 0.0, text_format)
                sheet_sold.write(row, 5, line.sold_amount or 0.0, money_format)
                sheet_sold.write(row, 6, line.order_count or 0, text_format)
                sheet_sold.write(row, 7, line.qty_available or 0.0, text_format)
                sheet_sold.write(row, 8, line.list_price or 0.0, money_format)
                if line.last_sale_date:
                    sheet_sold.write_datetime(row, 9, line.last_sale_date, date_format)
                else:
                    sheet_sold.write(row, 9, '', text_format)
                sheet_sold.write(row, 10, line.last_sale_price or 0.0, money_format)
                row += 1

        if self.report_type in ('both', 'unsold'):
            sheet_unsold = workbook.add_worksheet('Unsold Products')
            headers_unsold = ['Product Name', 'Internal Reference', 'Product Category', 'Internal Category', 'Quantity On Hand', 'Sales Price', 'Last Sale Date (Any Time)', 'Last Sale Price']
            for col_num, header in enumerate(headers_unsold):
                sheet_unsold.write(0, col_num, header, header_format)
            sheet_unsold.set_column(0, 0, 30)
            sheet_unsold.set_column(1, 7, 15)

            row = 1
            for line in self.unsold_line_ids.sorted(lambda l: l.product_name or ''):
                sheet_unsold.write(row, 0, line.product_name or '', text_format)
                sheet_unsold.write(row, 1, line.default_code or '', text_format)
                sheet_unsold.write(row, 2, line.categ_id.display_name or '', text_format)
                sheet_unsold.write(row, 3, line.internal_category_id.display_name or '', text_format)
                sheet_unsold.write(row, 4, line.qty_available or 0.0, text_format)
                sheet_unsold.write(row, 5, line.list_price or 0.0, money_format)
                if line.last_sale_date:
                    sheet_unsold.write_datetime(row, 6, line.last_sale_date, date_format)
                else:
                    sheet_unsold.write(row, 6, '', text_format)
                sheet_unsold.write(row, 7, line.last_sale_price or 0.0, money_format)
                row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name.replace(' ', '_')}.xlsx",
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class SoldUnsoldReportLine(models.Model):
    _name = 'sold.unsold.products.report.line'
    _description = 'Sold & Unsold Products Report Line'
    _order = 'product_name'

    report_id = fields.Many2one('sold.unsold.products.report', string='Report',
                                 required=True, ondelete='cascade')
    line_type = fields.Selection([
        ('sold', 'Sold'),
        ('unsold', 'Unsold'),
    ], string='Type', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_name = fields.Char(string='Product Name', related='product_id.display_name', store=True)
    default_code = fields.Char(string='Internal Reference', related='product_id.default_code', store=True)
    categ_id = fields.Many2one('product.category', string='Product Category',
                                related='product_id.categ_id', store=True)
    internal_category_id = fields.Many2one('internal.category', string='Internal Category',
                                            related='product_id.internal_category', store=True)
    qty_available = fields.Float(string='Quantity On Hand', related='product_id.qty_available')
    list_price = fields.Float(string='Sales Price', related='product_id.list_price')
    last_sale_date = fields.Date(string='Last Sale Date')
    last_sale_price = fields.Float(string='Last Sale Price')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   related='product_id.currency_id')

    # Sold-specific fields
    sold_qty = fields.Float(string='Qty Sold')
    sold_amount = fields.Float(string='Total Sales Amount')
    order_count = fields.Integer(string='No. of Orders')
