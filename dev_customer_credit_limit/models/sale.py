# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, models, fields

class sale_order(models.Model):
    _inherit= 'sale.order'
    
    exceeded_amount = fields.Float('Exceeded Amount')

    state = fields.Selection(selection_add=[
         ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('waiting_approval', 'Waiting Approval'),
        ('credit_limit', 'Credit limit'),
        ('rejected', 'Rejected'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
        
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(sale_order,self).onchange_partner_id()
        partner_id = self.partner_id
        if self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id
            
        if partner_id:
            if partner_id.credit_limit_on_hold:
                msg = "Customer '" + partner_id.name + "' is on credit limit hold."
                return {'warning':
                            {'title': 'Credit Limit On Hold', 'message': msg
                             }
                        }
    
    def action_sale_ok(self):
        partner_id = self.partner_id
        if self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id
        partner_ids = [partner_id.id]
        for partner in partner_id.child_ids:
            partner_ids.append(partner.id)
        
        if partner_id.check_credit:
            domain = [
                ('order_id.partner_id', 'in', partner_ids),
                ('order_id.state', 'in', ['sale', 'credit_limit','done'])]
            order_lines = self.env['sale.order.line'].search(domain)
            today = fields.Date.from_string(fields.Date.today())

            order = []
            to_invoice_amount = 0.0
            to_invoice_day = 0
            new_so_day = fields.Date.from_string(self.date_order)
            to_so_day = (today - new_so_day).days
            for line in order_lines:
                # Check if this order line has cancelled picking
                line_moves = line.move_ids
                cancelled_moves = line_moves.filtered(lambda move: move.state == 'cancel')
                """
                    Jika total not_invoiced itu lebih kecil dari 0 maka ubah nilai ke 0 untuk perhitungan compute_all
                    # Prepare For Case qty_to_order = 10
                    * Case 1: Picking 1 -> Done -> qty_done 8 sisa 2 (dari qty_to_order)
                              Picking 2 -> Cancel -> qty_done 0 qty_demand 2 
                """
                qty_invoiced = line.qty_invoiced + sum( cancelled_moves.mapped('product_uom_qty') )
                not_invoiced = line.product_uom_qty - qty_invoiced
                if not_invoiced > line.product_uom_qty or not_invoiced < 0:
                    not_invoiced = 0 
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(
                    price, line.order_id.currency_id,
                    not_invoiced,
                    product=line.product_id, partner=line.order_id.partner_id)
                if line.order_id.id not in order:
                    if line.order_id.invoice_ids:
                        for inv in line.order_id.invoice_ids:
                            if inv.state == 'draft':
                                order.append(line.order_id.id)
                                break
                    else:
                        order.append(line.order_id.id)
                """ ~ jika line ini udah pernah dikirim atau backorder 
                    ~ maka to_invoice_amount diisi. /
                    
                    ~ atau jika line ini hanya dicancel DO nya dan tidak pernah ada pengiriman
                    ~ maka to_invoice_amount tidak diisi.
                    
                    ~ jika SO yang udah di confirm belum ada pengiriman sama sekali
                    ~ maka to_invoice_amount diisi.
                """
                # if (line_moves - cancelled_moves) or not line_moves:
                to_invoice_amount += taxes['total_included']
            
            #DAY ON CONFIRMED SALES
            first_orders = self.search([('id','in',order)], order='date_order asc', limit=1)
            #print ("====first_orders====",first_orders)
            if first_orders:
                renew_so_date = fields.Date.from_string(first_orders.date_order)
                to_invoice_day = 0
                # udah gapake SO Days untuk credit limit by days
                # to_invoice_day = (today - renew_so_date).days

            domain = [
                ('move_id.partner_id', 'in', partner_ids),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '!=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                to_invoice_amount += taxes['total_included']

            # We sum from all the invoices lines that are in draft and not linked
            # to a sale order
            domain = [
                ('move_id.partner_id', 'in', partner_ids),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            draft_invoice_lines_amount = 0.0
            draft_invoice_lines_day = 0
            invoice=[]
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                tax = line.tax_ids or line.tax_line_id
                taxes = tax.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                if taxes['total_included'] > 0:
                    draft_invoice_lines_amount += taxes['total_included']
                    if line.move_id.id not in invoice:
                        invoice.append(line.move_id.id)

            draft_invoice_lines_amount = "{:.2f}".format(draft_invoice_lines_amount)
            to_invoice_amount = "{:.2f}".format(to_invoice_amount)
            draft_invoice_lines_amount = float(draft_invoice_lines_amount)
            to_invoice_amount = float(to_invoice_amount)
            # available_credit = (partner_id.credit_limit - partner_id.credit - to_invoice_amount - draft_invoice_lines_amount) - self.amount_total
            #DAY ON DRAFT INVOICE
            first_invoices = self.env['account.move'].search([('id','in',invoice)], order='invoice_date asc', limit=1)
            if first_invoices:
                renew_inv_date = fields.Date.from_string(first_invoices.invoice_date)
                if renew_inv_date:
                    draft_invoice_lines_day = (today-renew_inv_date).days
            available_day = self.partner_id.credit_day_limit - \
                self.partner_id.day_limit - \
                to_invoice_day - draft_invoice_lines_day
            #AVAILABLE = CREDIT LIMIT - CREDIT AR - OPEN INVOICE - DRAFT INVOICE
            available_credit = self.partner_id.credit_limit - \
                self.partner_id.credit - \
                to_invoice_amount - draft_invoice_lines_amount - self.amount_total
            #print ("==available_credit==",self.amount_total,available_credit,self.partner_id.credit_day_limit,self.partner_id.day_limit,to_invoice_day,draft_invoice_lines_day,available_day)

            if (available_day < 0):
                imd = self.env['ir.model.data'].sudo()
                exceeded_amount = (to_invoice_amount + draft_invoice_lines_amount + partner_id.credit + self.amount_total) - partner_id.credit_limit
                exceeded_amount = "{:.2f}".format(exceeded_amount)
                exceeded_amount = float(exceeded_amount)
                imd = self.env['ir.model.data']
                exceeded_day = (to_invoice_day + draft_invoice_lines_day + self.partner_id.day_limit + to_so_day) - self.partner_id.credit_day_limit
                vals_wiz={
                    'partner_id': self.partner_id.id,
                    'sale_orders': str(len(order))+ ' Sale Order Worth : '+ str(to_invoice_day) + ' Day(s)',
                    'invoices': str(len(invoice))+' Draft Invoice worth : '+ str(draft_invoice_lines_day) + ' Day(s)',
                    'current_sale_day': str(to_so_day) + ' Day(s)',
                    'exceeded_day': str(exceeded_day) + ' Day(s)',
                    'credit_day': str(self.partner_id.day_limit) + ' Day(s)',
                    'credit_limit_on_hold': self.partner_id.credit_limit_on_hold,
                    }
                #print ("==vals_wiz==",vals_wiz)
                wiz_id=self.env['customer.limit.wizard'].create(vals_wiz)
                # action = imd.xmlid_to_object('dev_customer_credit_limit.action_customer_limit_wizard')
                # form_view_id=imd.xmlid_to_res_id('dev_customer_credit_limit.view_customer_limit_day_wizard_form')
                # action = self.env.ref('dev_customer_credit_limit.action_customer_limit_wizard').read()[0]
                action = self.env['ir.actions.actions']._for_xml_id('dev_customer_credit_limit.action_customer_limit_wizard')
                action['views'] = [(self.env.ref('dev_customer_credit_limit.view_customer_limit_wizard_form').id, 'form')]
                action['res_id'] = wiz_id.id
                # return  {
                #         'name': action.name,
                #         'help': action.help,
                #         'type': action.type,
                #         'views': [(form_view_id, 'form')],
                #         'view_id': form_view_id,
                #         'target': action.target,
                #         'context': action.context,
                #         'res_model': action.res_model,
                #         'res_id':wiz_id.id,
                #     
                return action
            elif available_credit < 0:
                imd = self.env['ir.model.data'].sudo()
                exceeded_amount = (to_invoice_amount + draft_invoice_lines_amount + partner_id.credit + self.amount_total) - partner_id.credit_limit
                exceeded_amount = "{:.2f}".format(exceeded_amount)
                exceeded_amount = float(exceeded_amount)
                currency = draft_invoice_lines.mapped('currency_id')
                vals_wiz={
                    'partner_id':partner_id.id,
                    'sale_orders':str(len(order))+ ' Sale Order Worth : '+  "{:,.2f}".format(to_invoice_amount),
                    'invoices':str(len(invoice))+' Draft Invoice worth : ' + "{:,.2f}".format(draft_invoice_lines_amount),
                    'current_sale':self.amount_total or 0.0,
                    'exceeded_amount':exceeded_amount,
                    'credit':partner_id.credit,
                    'credit_limit_on_hold':partner_id.credit_limit_on_hold,
                    }
                wiz_id = self.env['customer.limit.wizard'].create(vals_wiz)
                # action = self.env.ref('dev_customer_credit_limit.action_customer_limit_wizard').read()[0]
                action = self.env['ir.actions.actions']._for_xml_id('dev_customer_credit_limit.action_customer_limit_wizard')
                #action['views'] = [(self.env.ref('account.view_account_payment_form').id, 'form')]
                #action['res_id'] = invoices.ids[0]
                # action = imd.xmlid_to_object('dev_customer_credit_limit.action_customer_limit_wizard')
                # form_view_id = imd.xmlid_to_res_id('dev_customer_credit_limit.view_customer_limit_wizard_form')
                #print ('==res_model==',action)
                action['views'] = [(self.env.ref('dev_customer_credit_limit.view_customer_limit_wizard_form').id, 'form')]
                action['res_id'] = wiz_id.id
                # action = {
                #         'name': action.name,
                #         'help': action.help,
                #         'type': action.type,
                #         'views': [(self.env.ref('dev_customer_credit_limit.action_customer_limit_wizard').id, 'form')],
                #         'view_id': form_view_id,
                #         'target': action.target,
                #         'context': action.context,
                #         'res_model': action.res_model,
                #         'res_id': wiz_id.id,
                # }
                return action
            else:
                # back to button approve for checking approval matrix
                self.action_confirm()
        else:
            # back to button approve for checking approval matrix
            self.action_confirm()
        return True
        
        
    def _make_url(self,model='sale.order'):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url', default='http://localhost:8069')
        if base_url:
            base_url += '/web/login?db=%s&login=%s&key=%s#id=%s&model=%s' % (self._cr.dbname, '', '', self.id, model)
        return base_url

    def send_mail_approve_credit_limit(self): 
        # Email notification disabled per user request
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
