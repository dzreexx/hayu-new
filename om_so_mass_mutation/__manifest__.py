{
    'name': 'Mass SO Mutation Wizard',
    'version': '15.0.1.0.0',
    'summary': 'Konsolidasi kekurangan stok dari banyak Sales Order menjadi satu draf Internal Transfer',
    'category': 'Sales/Inventory',
    'author': 'Muhamad Zulfikar Ali Salim',
    'depends': ['sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mass_mutation_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}