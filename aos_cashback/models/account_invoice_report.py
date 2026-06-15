from odoo import models,api,fields,_
from odoo.exceptions import UserError
from odoo.tools import float_compare
import json

class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    # customer_group_id = fields.Many2one("adireksa.customer.target", related="move_id.customer_group_id",string="Customer Group",readonly=True,store=True)
    customer_group_id = fields.Many2one("adireksa.customer.target", string="Customer Group", readonly=True)
    def _select(self):
          res = super(AccountInvoiceReport,self)._select()
          res += """,move.customer_group_id"""
          return res
    
    # def _select(self):
    #     return super()._select() + ", contact_partner.group_id as group_id"

    # def _from(self):
    #     return super()._from() + " LEFT JOIN res_partner contact_partner ON contact_partner.id = move.partner_id"

    def _select_additional_fields(self,fields):
        res = super(AccountInvoiceReport,self)._select_additional_fields(fields)
        res['customer_group_id'] = """,move.customer_group_id"""   
        return res