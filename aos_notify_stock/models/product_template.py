# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_per_month = fields.Integer(string="Qty Sales Per",store=True)
    sales_qty_count = fields.Integer(compute='_compute_sales_qty',store=True)

    status = fields.Selection([('normal','Normal'),('excess','Excess'),('reorder','Re-order')], 
       string='Status', default='normal',store=True)
    incoming_qty = fields.Integer(string="Incoming Qty",compute="_compute_incoming_qty",store=True)

    @api.depends('product_variant_ids.qty_available','product_variant_id.qty_available')
    def _compute_incoming_qty(self):
        for rec in self:
            rec.sudo().incoming_qty = rec.product_variant_id.incoming_qty


    def min_months(self,sourcedate, months):
        month = sourcedate.month - months
        year = sourcedate.year - (month if month != 0 else 12) // 12
        month = month % 12 if month != 0 else 12
        if month == 0 :
            month = 6
        day = sourcedate.day
        date = f'{year}-{month}-{day}'
        try:
            return fields.Date.from_string(date)
        except ValueError:
            if month == 2 and day > 28:
                day = 28
                date = f'{year}-{month}-{day}'
            else :
                day = calendar.monthrange(year,month)[1]
                date = f'{year}-{month}-{day}'
            return fields.Date.from_string(date)

    # def min_months(self,sourcedate, months):
    #     month = sourcedate.month - months
    #     year = sourcedate.year - (month if month != 0 else 12) // 12
    #     month = month % 12 if month != 0 else 12
    #     day = sourcedate.day
        
    #     last_day_of_month = monthrange(year, month)[1]
    #     if day > last_day_of_month:
    #         day = last_day_of_month
    #     #date = f'{year}-{month}-{day}'
    #     try:
    #         return fields.Date.from_string(date)
    #     except ValueError:
    #         # #if month == 2 and day > 28:
    #         #     day = 28
    #         #     date = f'{year}-{month}-{day}'
    #         # elif month == 10 and day >= 31 :
    #         #     day = 31
    #         #     date = f'{year}-{month}-{day}'
    #         # return fields.Date.from_string(date)


    @api.depends('sale_per_month','qty_on_hand_query','product_variant_ids.qty_available')
    def _compute_sales_qty(self):
        for rec in self:
            target_date = fields.datetime.today() - relativedelta(months=rec.sale_per_month or 0)
            sale_line_obj = self.env['sale.order.line'].search([('product_id.product_tmpl_id','in',rec.ids),('order_id.date_order','>=', target_date)])
            rec.sales_qty_count = sum(sale_line_obj.mapped('qty_delivered'))
            # update calculation
            # (On Hand + Incoming Qty) operator _percent_ * qty_sales
            # Batas bawah normal (On hand + Incoming) = 80% x qty sales			
            # Batas atas normal (On hand + Incoming) = 120% x qty sales			
            # Reorder (On hand + Incoming) < 80% x qty sales	
            # excess (On hand + Incoming) > 120% x qty sales		
            quantity = rec.qty_on_hand_query + rec.outstanding_qty
            upper_limit = (120 / 100) * rec.sales_qty_count
            lower_limit = (80 / 100) * rec.sales_qty_count
            
            if quantity < lower_limit:
                rec.sudo().write({'status':'reorder'})
            elif quantity > upper_limit:
                rec.sudo().write({'status':'excess'})
            else:
                rec.sudo().write({'status':'normal'})
                
            # persen_atas = self.env['ir.config_parameter'].sudo().get_param('aos_notify_stock.batas_atas')
            # persen_bawah = self.env['ir.config_parameter'].sudo().get_param('aos_notify_stock.batas_bawah')
            # Backup Code
            # batas_atas  = rec.sales_qty_count + ((rec.sales_qty_count / 100) * int(persen_atas))
            # batas_bawah = rec.sales_qty_count - ((rec.sales_qty_count / 100) * int(persen_bawah))
            # if ( rec.qty_on_hand_query + rec.outstanding_qty ) > batas_atas:
            #     rec.sudo().write({'status':'excess'})
            # elif ( rec.qty_on_hand_query + rec.outstanding_qty ) < batas_bawah :
            #     rec.sudo().write({'status':'reorder'})
            # else:
            #     rec.sudo().write({'status':'normal'})

    def _search_qty_available_query(self, operator, value):
        domain = [('qty_available', operator, value)]
        product_variant_query = self.env['product.product']._search(domain)
        return [('product_variant_ids', 'in', product_variant_query)]

class ProductProduct(models.Model):
    _inherit = "product.product"

    barcode = fields.Char(
        'Barcode', copy=False,
        help="International Article Number used for product identification.",store=True)