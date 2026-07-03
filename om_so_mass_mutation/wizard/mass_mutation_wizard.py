from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrderMutationWizard(models.TransientModel):
    _name = 'sale.order.mutation.wizard'
    _description = 'Wizard Mutasi Massal'

    # Field untuk memilih lokasi asal dan tujuan secara manual di wizard (opsional/fleksibel)
    location_id = fields.Many2one('stock.location', string='Source Location (Gudang)', required=True, domain=[('usage', '=', 'internal')])
    location_dest_id = fields.Many2one('stock.location', string='Destination Location (Toko)', required=True, domain=[('usage', '=', 'internal')])

    def generate_consolidated_mutation(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError("Tidak ada Sales Order yang dipilih.")

        orders = self.env['sale.order'].browse(active_ids)
        lines_to_mutate = {}

        for order in orders:
            # Validasi status SO
            if order.state not in ['sale', 'done']:
                continue
                
            for line in order.order_line:
                # Hanya proses produk berjenis Storable Product
                if line.product_id.type != 'product':
                    continue
                
                # Cek stok aktual di Toko (Destination Location)
                qty_available_in_toko = line.product_id.with_context(location=self.location_dest_id.id).qty_available
                
                # Jika stok di toko kurang dari yang diminta oleh SO
                if qty_available_in_toko < line.product_uom_qty:
                    needed_qty = line.product_uom_qty - qty_available_in_toko
                    
                    # Gabungkan kuantitas jika ada produk yang sama dari SO yang berbeda
                    if line.product_id.id in lines_to_mutate:
                        lines_to_mutate[line.product_id.id] += needed_qty
                    else:
                        lines_to_mutate[line.product_id.id] = needed_qty

        if not lines_to_mutate:
            raise UserError("Semua stok di Lokasi Toko mencukupi untuk Sales Order yang dipilih.")

        # Cari Picking Type untuk Internal Transfer
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        if not picking_type:
            raise UserError("Picking Type untuk 'Internal Transfer' tidak ditemukan.")

        # Buat draf dokumen Internal Transfer (Picking)
        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'origin': f"Mutasi Massal Kelompok SO: {', '.join(orders.mapped('name'))}",
            'move_ids_without_package': [
                (0, 0, {
                    'name': self.env['product.product'].browse(prod_id).name,
                    'product_id': prod_id,
                    'product_uom_qty': qty, # Ini masuk ke kolom DEMAND (Permintaan)
                    'product_uom': self.env['product.product'].browse(prod_id).uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                }) for prod_id, qty in lines_to_mutate.items()
            ]
        }
        
        picking = self.env['stock.picking'].create(picking_vals)
        
        # CATATAN: Sengaja TIDAK memanggil action_confirm() atau action_assign()
        # Agar status benar-benar DRAFT dan jumlah di kolom DONE kosong (harus diisi manusia).

        # Buka langsung form dokumen yang baru terbuat biar user bisa cek
        return {
            'name': 'Draf Mutasi Terbuat',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }