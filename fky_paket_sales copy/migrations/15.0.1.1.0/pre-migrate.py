# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute("""
        CREATE TABLE IF NOT EXISTS fky_paket_sales_template_internal_category_rel (
            fky_paket_sales_template_id INTEGER NOT NULL,
            internal_category_id INTEGER NOT NULL,
            CONSTRAINT fky_paket_sales_template_internal_category_rel_pk
                PRIMARY KEY (fky_paket_sales_template_id, internal_category_id)
        );
    """)
    cr.execute("""
        INSERT INTO fky_paket_sales_template_internal_category_rel
            (fky_paket_sales_template_id, internal_category_id)
        SELECT id, internal_category_id
        FROM fky_paket_sales_template
        WHERE internal_category_id IS NOT NULL
        ON CONFLICT DO NOTHING;
    """)
    cr.execute("""
        ALTER TABLE fky_paket_sales_template
        DROP COLUMN IF EXISTS internal_category_id;
    """)
