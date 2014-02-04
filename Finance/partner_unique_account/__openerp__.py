{
    'name': 'Test',
    'version': '1.0',
    'category': 'Certification',
    'description': """
               test task....  
 """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ['base','sale'],
    'data': [
             'wizard/create_account_view.xml',
             'wizard/sequence.xml',
             'res_partner_view.xml',
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
