{
    'name': 'Approver by admin',
    'version': '1.0',
    'category': 'Certification',
    'description': """
                 This module send mail to Admin for approval Documents  
 """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ['base','project','mail'],
    'data': [
             'security/permission_to_user.xml',
             'security/ir.model.access.csv',
             'admin_approver_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
