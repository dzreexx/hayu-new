# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ---- Field untuk Delivery Order (menandai kebutuhan mutasi) ----
    # PENTING: field ini COMPUTED & STORED. Nilainya otomatis dihitung ulang
    # berdasarkan kondisi stok saat ini, bukan diisi manual lewat tombol.
    # Tombol "Cek & Buat Mutasi" hanya bertugas MEMBUAT dokumen Internal
    # Transfer -- bukan menentukan status yes/no ini.
    need_mutation = fields.Selection(
        selection=[
            ('no', 'No'),
            ('yes', 'Yes'),
        ],
        string='Need Mutation',
        compute='_compute_need_mutation',
        store=True,
        copy=False,
        tracking=True,
        help="Otomatis 'Yes' jika ada produk di Delivery Order ini yang stoknya "
             "kurang di lokasi asal (misal TOKO). Otomatis kembali 'No' jika: "
             "stok sudah cukup, Delivery Order sudah Done/Cancelled, atau sudah "
             "ada Internal Transfer (mutasi) yang dibuat untuk menutupinya.",
    )
    mutation_transfer_ids = fields.Many2many(
        comodel_name='stock.picking',
        relation='stock_picking_mutation_rel',
        column1='delivery_picking_id',
        column2='mutation_picking_id',
        string='Mutation Transfers',
        copy=False,
        help="Dokumen Internal Transfer (mutasi) yang dibuat otomatis untuk "
             "menutupi kekurangan stok Delivery Order ini.",
    )

    # ---- Field untuk dokumen Internal Transfer hasil auto mutation ----
    is_mutation_transfer = fields.Boolean(
        string='Auto Mutation Transfer',
        default=False,
        copy=False,
        help="Ditandai otomatis jika picking ini adalah Internal Transfer "
             "yang dibuat oleh fitur 'Cek & Buat Mutasi'.",
    )
    source_delivery_ids = fields.Many2many(
        comodel_name='stock.picking',
        relation='stock_picking_mutation_rel',
        column1='mutation_picking_id',
        column2='delivery_picking_id',
        string='Delivery Order Terkait',
        copy=False,
        help="Delivery Order yang menjadi pemicu dibuatnya mutasi/internal "
             "transfer ini.",
    )

    # ------------------------------------------------------------------
    # COMPUTE: status Need Mutation
    # ------------------------------------------------------------------
    @api.depends(
        'picking_type_id.code',
        'state',
        'move_lines.product_id',
        'move_lines.product_uom_qty',
        'move_lines.state',
        'mutation_transfer_ids.state',
    )
    def _compute_need_mutation(self):
        for picking in self:
            # Bukan Delivery Order, atau sudah selesai/batal -> tidak relevan lagi
            if picking.picking_type_id.code != 'outgoing' or picking.state in ('done', 'cancel'):
                picking.need_mutation = 'no'
                continue

            # Sudah ada Internal Transfer (mutasi) aktif (bukan cancel) yang
            # dibuat untuk menutupi kekurangan DO ini -> anggap sudah
            # ditindaklanjuti, tidak perlu ditandai 'Yes' lagi
            active_mutations = picking.mutation_transfer_ids.filtered(
                lambda m: m.state != 'cancel'
            )
            if active_mutations:
                picking.need_mutation = 'no'
                continue

            picking.need_mutation = 'yes' if picking._get_shortage_by_product() else 'no'

    def _get_shortage_by_product(self):
        """Hitung kekurangan stok per produk untuk 1 Delivery Order (self),
        dibandingkan dengan stok on-hand di lokasi asal DO tersebut.

        Return: dict {product.product: shortage_qty (float)}.
        Hanya berisi produk yang qty diminta > qty on-hand di lokasi asal.
        """
        self.ensure_one()
        result = {}

        if self.picking_type_id.code != 'outgoing' or self.state in ('done', 'cancel'):
            return result

        source_location = self.location_id  # lokasi asal barang dikirim, mis. TOKO ADIREKSA/Stock

        for move in self.move_lines:
            if move.state in ('done', 'cancel'):
                continue
            product = move.product_id
            if not product or product.type != 'product':
                continue
            qty_needed = move.product_uom_qty
            if qty_needed <= 0:
                continue

            qty_on_hand = product.with_context(location=source_location.id).qty_available
            shortage_qty = qty_needed - qty_on_hand

            if shortage_qty > 0:
                result[product] = result.get(product, 0.0) + shortage_qty

        return result

    # ------------------------------------------------------------------
    # CRON: paksa recompute need_mutation secara berkala
    # ------------------------------------------------------------------
    def _cron_refresh_need_mutation(self):
        """Dipanggil oleh scheduled action (tiap 15 menit). Memaksa
        recompute 'need_mutation' untuk semua Delivery Order yang masih
        aktif, supaya status tetap akurat walau kekurangan stok muncul
        akibat transaksi lain (bukan perubahan pada dokumen ini sendiri).
        """
        active_deliveries = self.search([
            ('picking_type_id.code', '=', 'outgoing'),
            ('state', 'not in', ('done', 'cancel')),
        ])
        active_deliveries._compute_need_mutation()

    # ------------------------------------------------------------------
    # ACTION: buat Internal Transfer (mutasi) untuk DO yang dipilih
    # ------------------------------------------------------------------
    def action_check_and_create_mutation(self):
        """Untuk Delivery Order yang dipilih (self), buat Internal Transfer
        yang teragregasi per pasangan lokasi stok (sumber -> tujuan), guna
        menutupi kekurangan stok yang sudah terdeteksi lewat need_mutation.

        Dipanggil dari menu Inventory > Delivery Orders (multi-select) atau
        dari tombol di form Delivery Order.

        Catatan: status 'Need Mutation' TIDAK ditentukan oleh action ini --
        field itu computed otomatis (lihat _compute_need_mutation). Action
        ini murni membuat dokumen transfer berdasarkan kekurangan yang ada
        saat ini.

        Alur:
          1. Hanya memproses picking bertipe 'outgoing' (Delivery Order)
             yang belum Done/Cancel. Picking lain dilewati dengan peringatan.
          2. Ambil kekurangan tiap DO lewat _get_shortage_by_product().
          3. Cari warehouse pasangan (mis. GUDANG) otomatis lewat
             stock.warehouse._get_resupply_warehouse().
          4. Semua kekurangan diagregasi lintas Delivery Order yang dipilih,
             lalu dibuat 1 Internal Transfer per pasangan lokasi, dengan
             tujuan lokasi Transit warehouse tujuan (bukan lokasi Stock
             utama). Dokumen dibuat sebagai Draft -- TIDAK di-confirm dan
             TIDAK di-validate -- supaya semua field (termasuk qty & lokasi)
             masih bisa dikoreksi manual sebelum diproses lebih lanjut.
          5. Setelah link mutation_transfer_ids terbentuk, need_mutation
             otomatis ter-recompute jadi 'No' (karena sudah ditindaklanjuti).
        """
        StockPicking = self.env['stock.picking']

        outgoing_pickings = self.filtered(
            lambda p: p.picking_type_id.code == 'outgoing' and p.state not in ('done', 'cancel')
        )
        ignored_pickings = self - outgoing_pickings

        # key: (source_location_id, dest_location_id)
        # val: { product_id: {'qty': float, 'delivery_ids': set()} }
        shortage_map = defaultdict(lambda: defaultdict(lambda: {'qty': 0.0, 'delivery_ids': set()}))
        skipped_messages = []

        if ignored_pickings:
            skipped_messages.append(
                _("- %s dokumen dilewati karena bukan Delivery Order aktif (outgoing, belum Done/Cancel).")
                % len(ignored_pickings)
            )

        for picking in outgoing_pickings:
            store_wh = picking.picking_type_id.warehouse_id  # warehouse Toko (pemilik DO ini)
            fulfillment_location = picking.location_id  # lokasi yang dicek utk shortage, mis. TOKO/Stock

            if not store_wh:
                skipped_messages.append(
                    _("- %s: dilewati, picking type tidak terhubung ke warehouse.") % picking.name
                )
                continue

            shortage_by_product = picking._get_shortage_by_product()
            if not shortage_by_product:
                continue

            supply_wh = store_wh._get_resupply_warehouse()
            if not supply_wh:
                skipped_messages.append(
                    _("- %s: butuh mutasi, tapi warehouse '%s' tidak bisa otomatis "
                      "dipasangkan (ada lebih dari 2 warehouse aktif). Set 'Resupply From' "
                      "manual di Inventory > Configuration > Warehouses.")
                    % (picking.name, store_wh.name)
                )
                continue

            # Tujuan akhir mutasi BUKAN langsung ke lokasi Stock utama Toko,
            # tapi ke lokasi Transit Toko (mis. TKADR/Transit) dulu.
            final_dest_location = store_wh._get_mutation_dest_location()

            key = (supply_wh.lot_stock_id.id, final_dest_location.id)
            for product, qty in shortage_by_product.items():
                entry = shortage_map[key][product.id]
                entry['qty'] += qty
                entry['delivery_ids'].add(picking.id)

        # ---- Buat Internal Transfer per pasangan lokasi ----
        created_pickings = StockPicking

        for (src_loc_id, dest_loc_id), products_data in shortage_map.items():
            src_location = self.env['stock.location'].browse(src_loc_id)
            dest_location = self.env['stock.location'].browse(dest_loc_id)

            supply_wh = self.env['stock.warehouse'].search(
                [('lot_stock_id', '=', src_loc_id)], limit=1
            )
            picking_type = supply_wh.int_type_id if supply_wh else False

            if not picking_type:
                skipped_messages.append(
                    _("- Warehouse dengan lokasi stok %s tidak punya Internal Transfer "
                      "operation type, mutasi ke %s dilewati.")
                    % (src_location.display_name, dest_location.display_name)
                )
                continue

            move_vals_list = []
            all_delivery_ids = set()

            for product_id, data in products_data.items():
                product = self.env['product.product'].browse(product_id)
                all_delivery_ids |= data['delivery_ids']
                move_vals_list.append((0, 0, {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_uom_qty': data['qty'],
                    'product_uom': product.uom_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': dest_location.id,
                }))

            related_deliveries = StockPicking.browse(list(all_delivery_ids))

            picking = StockPicking.create({
                'picking_type_id': picking_type.id,
                'location_id': src_location.id,
                'location_dest_id': dest_location.id,
                'origin': ', '.join(related_deliveries.mapped('name')),
                'is_mutation_transfer': True,
                'source_delivery_ids': [(6, 0, related_deliveries.ids)],
                'move_lines': move_vals_list,
            })

            # SENGAJA dibiarkan status Draft -- TIDAK dipanggil action_confirm()
            # atau action_assign(). Kalau langsung di-confirm, Odoo mengunci
            # beberapa field di tiap move (termasuk source/destination
            # location) supaya konsisten dengan reservasi yang sudah jalan.
            # Karena qty/lokasi hasil deteksi otomatis ini masih perlu
            # dicek & mungkin dikoreksi manual oleh tim logistik (mis. tujuan
            # yang benar adalah lokasi Transit, bukan Stock), dokumen
            # sengaja dibiarkan Draft supaya semua field masih bisa diedit
            # bebas. Tim logistik yang akan klik Confirm & Validate sendiri
            # setelah selesai mengecek/mengoreksi.

            created_pickings |= picking
            related_deliveries.write({'mutation_transfer_ids': [(4, picking.id)]})

        # ---- Notifikasi hasil ke user ----
        if not shortage_map and not skipped_messages:
            message_lines = [_("Tidak ada kekurangan stok yang terdeteksi pada dokumen yang dipilih.")]
        else:
            message_lines = [
                _("%s dokumen Internal Transfer (mutasi) berhasil dibuat sebagai Draft. "
                  "Silakan cek qty & lokasi, lalu Confirm manual.")
                % len(created_pickings)
            ]
            if created_pickings:
                message_lines.append(', '.join(created_pickings.mapped('name')))
        if skipped_messages:
            message_lines.append(_("\nPerhatian:"))
            message_lines.extend(skipped_messages)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cek & Buat Mutasi Selesai'),
                'message': '\n'.join(message_lines),
                'sticky': bool(skipped_messages),
                'type': 'success' if created_pickings else 'warning',
            }
        }
