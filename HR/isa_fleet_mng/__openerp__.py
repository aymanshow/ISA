{
    'name': 'Vehicle Incident Tracking',
    'version': '1.0',
    'category': 'Certification',
    'description': """
               This module will use to track the accident of vehicle  
 """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ['base','fleet'],
    'data': [
             'form_sequence.xml',
             'vehicle_accident_tracking_view.xml'
             
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
