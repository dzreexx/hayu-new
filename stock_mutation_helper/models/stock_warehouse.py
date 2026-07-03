# -*- coding: utf-8 -*-
from odoo import models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def _get_resupply_warehouse(self):
        """Cari warehouse pasangan (sumber mutasi) untuk warehouse ini,
        TANPA perlu field konfigurasi tambahan.

        Prioritas:
          1. Field native Odoo 'resupply_wh_ids' (menu Warehouse >
             tab config 'Resupply From'), kalau sudah diisi 1 warehouse.
          2. Kalau company hanya punya 2 warehouse aktif total (misal
             TOKO ADIREKSA & GUDANG ADIREKSA), otomatis pakai warehouse
             yang satu lagi -- tidak perlu setting apa pun.

        Return: recordset stock.warehouse (kosong kalau tidak bisa
        ditentukan otomatis, misal ada >2 warehouse tanpa 'Resupply From').
        """
        self.ensure_one()

        if self.resupply_wh_ids and len(self.resupply_wh_ids) == 1:
            return self.resupply_wh_ids

        other_warehouses = self.search([
            ('company_id', '=', self.company_id.id),
            ('id', '!=', self.id),
        ])
        if len(other_warehouses) == 1:
            return other_warehouses

        return self.browse()

    def _get_mutation_dest_location(self):
        """Cari lokasi tujuan akhir untuk mutasi masuk ke warehouse ini.

        Prioritas:
          1. Lokasi anak dari warehouse ini yang namanya mengandung
             'Transit' (mis. TKADR/Transit) -- barang mutasi transit di
             sini dulu sebelum masuk ke rak/Stock utama.
          2. Kalau tidak ketemu, fallback ke lot_stock_id (lokasi Stock
             utama warehouse ini) seperti sebelumnya.

        Return: recordset stock.location (tidak pernah kosong, selalu ada
        fallback).
        """
        self.ensure_one()

        transit_location = self.env['stock.location'].search([
            ('location_id', 'child_of', self.view_location_id.id),
            ('name', '=ilike', 'Transit'),
        ], limit=1)

        return transit_location or self.lot_stock_id
