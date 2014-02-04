# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Isa Account',
    'version': '1.1',
    'author': 'DrishtiTech',
    'category': 'Accounting',
    'sequence': 21,
    'website': 'http://www.drishtitech.com',
    'summary': 'Customization Of account and invoices',
    'description': """
         Create a new menu My Task
         """,
 
    'images': [
               ],
    'depends': ['base', 'account','account_voucher','partner_unique_account'],
    'data': [    'wizard/report_wizard_view.xml',
                'wizard/account_wizard_view.xml',
                'data.xml',
     #           'security/ir.model.access.csv',
                 'account_view.xml',
                 'account_report.xml',
                 
                
                 
                 ],
    'demo': ['data.xml'],
    'test': [  
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'css': [  ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: