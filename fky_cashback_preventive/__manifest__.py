{
    'name': 'FKY Cashback Preventive',
    'version': '14.0.1.0.0',
    'category': 'Sales',
    'summary': 'Prevent Cashback Generation More Than Once',
    'description': """This module prevents cashback omzet target from generating more than once...""",
    'author': 'Fukuy',
    'depends': ['aos_cashback'],
    'data': [
        'views/cashback_rule.xml',
    ],
    'installable': True,
    'auto_install': False,
}
