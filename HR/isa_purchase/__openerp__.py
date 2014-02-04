{
    'name': 'ISA - Purchase Management',
    'version': '1.0',
    'category': 'Purchase Management',
    'summary': 'Status Of All the task which are in process or processed',
    'description':'hello',
    'author': 'Drishti Tech',
    'website': 'http://www.drishtitech.com',
    'depends': ['base','purchase','stock','account_voucher','account'],
    'data': [
#              'sequence.xml',
#              'wizard/pnl_wizard_view.xml',
             'purchase_view.xml',
             'data/clearing_agent_template.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
