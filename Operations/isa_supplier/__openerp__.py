{
    'name': ' Supplier Certification',
    'version': '1.0',
    'category': 'Certification',
    'description': """
               This module send mail to users for notification of their Production expire. 
 """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ['base','product',],
    'data': [
             'supplier_certification_view.xml',
             'test_schedular.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
