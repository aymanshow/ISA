
{
    'name': 'ISA Office Management',
    'version': '0.9',
    'category': 'Company',
    'description': """.
===================================================
""",
    'author': 'Drishti Tech',
    'maintainer': 'Drishti Tech',
    'website': 'http://www.openerp.com',
    'depends': ['base','hr','product','stock',],
    'data': [
             'form_sequence.xml',
             'wizard/appointment_wizard_view.xml',
            'office_view.xml',
            'room_type_view.xml',
            ],
    'installable': True,
    'auto_install': False,
}