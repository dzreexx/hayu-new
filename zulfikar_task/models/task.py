# from typing import Required
from odoo import models, fields

class ZulfikarTask(models.Model):
    _name = "zulfikar.task"
    _description = "data apaan aja dah terserah di store orang cuma buat test doang"

    name = fields.Char(string='Judulnye', required=True)
    description = fields.Text(string="Deskripsinye", required=True)
    date = fields.Date(string="Tanggalnye")
    is_done = fields.Boolean(string="Selesai ?", default=False)