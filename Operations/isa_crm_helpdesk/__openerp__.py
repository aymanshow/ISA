{
    'name': 'Crm Service',
    'version': '1.0',
    'category': 'Certification',
    'description': """
               This module will use for provide service to customer.  
 """,
    'author': 'Drishtitech',
    'website': 'http://www.openerp.com',
    'depends': ['base','crm_helpdesk'],
    'data': [
             'crm_helpdesk_cstm_view.xml',
             'form_sequence.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
