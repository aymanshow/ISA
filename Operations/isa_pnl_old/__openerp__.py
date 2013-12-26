{
    'name': 'ISA - P&L Module',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'P&L creation during Sales process',
    'description':'hello',
    'author': 'Drishti Tech',
    'website': 'http://www.drishtitech.com',
    'depends': ['sale', 'crm', 'purchase','account_budget','sale_crm','project','purchase_requisition'],
    'data': [
             'sequence.xml',
             'wizard/pnl_wizard_view.xml',
             'pnl_view.xml',
             'data.xml'
             ],
    'demo': [
            'data.xml' 
            ],
    'update':[
              'data.xml' 
              ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
