# -*- coding: utf-8 -*-
{
    'name': 'Stock Mutation Helper (Auto Detect Mutasi dari Sales Order)',
    'version': '15.0.1.0.0',
    'summary': 'Deteksi otomatis kebutuhan mutasi stok antar warehouse dari Delivery Order '
                'dan membuat Internal Transfer (Draft, ke lokasi Transit, tidak auto-confirm).',
    'description': """
Stock Mutation Helper
======================
Module ini membantu tim logistik yang mengelola 2 warehouse (misal: Toko & Gudang)
untuk otomatis mendeteksi produk yang kurang stok di warehouse Toko lewat
Delivery Order (Inventory), lalu membuat dokumen Internal Transfer dari Gudang
ke lokasi Transit Toko sebagai Draft. User tetap perlu mengecek qty & lokasi,
lalu confirm dan validate manual.

Fitur:
------
- Field baru "Need Mutation" (Yes/No) langsung di Delivery Order (Inventory),
  tempat tim logistik bekerja sehari-hari -- bukan di Sales Order. Field ini
  computed otomatis (bukan diisi manual lewat tombol).
- TIDAK perlu setup field warehouse baru: modul otomatis mendeteksi pasangan
  warehouse (misal TOKO ADIREKSA <-> GUDANG ADIREKSA) selama cuma ada 2
  warehouse aktif, atau memakai field native Odoo 'Resupply From' kalau ada
  lebih dari 2 warehouse.
- Tujuan mutasi otomatis diarahkan ke lokasi Transit warehouse tujuan (mis.
  TKADR/Transit) kalau lokasi tersebut ada, bukan langsung ke lokasi Stock.
- Action "Cek & Buat Mutasi" bisa dijalankan untuk banyak Delivery Order
  sekaligus (multi-select di list view), otomatis membuat 1 Internal Transfer
  teragregasi per pasangan lokasi stok.
- Internal Transfer dibuat sebagai Draft -- TIDAK di-confirm, TIDAK
  di-validate -- supaya semua field (qty, lokasi, dll) masih bisa dikoreksi
  manual oleh tim logistik sebelum diproses lebih lanjut.
- Tracking dokumen mutasi apa saja yang terhubung ke tiap Delivery Order,
  dan sebaliknya.
""",
    'category': 'Inventory/Inventory',
    'author': 'Custom Development',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'stock'],
    'data': [
        'data/ir_cron_data.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
