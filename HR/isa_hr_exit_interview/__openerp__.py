{
    'name': 'Employee Resignation form',
    'version': '1.0',
    'category': 'Certification',
    'description': """
               Employee send resign letter to his manager  
 """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ['base','hr','hr_contract'],
    'data': [
             'security/permission_to_user.xml',
             'security/ir.model.access.csv',
             'resign_information_view.xml',
             'wizard/wiz_employee_resign_view.xml',
             'employee_resignation_view.xml',
             'exit_interview_ques_view.xml'
             

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
