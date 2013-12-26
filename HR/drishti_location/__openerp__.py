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
    'name': 'Product Movement by Drishti Location',
    'version': '1.1',
    'author': 'Amit Gupta',
    'category': 'Stock',
    'sequence': 21,
    'website': 'http://www.drishtitech.com',
    'summary': 'Product Delivery to different different location base on requirement of product',
    'description': """
         Stock Movement
         """,
 
    'images': [
               ],
    'depends': ['base', 'stock','hr','purchase','purchase_requisition'],
    'data': [    'security/location_security_view.xml',
                 'security/ir.model.access.csv',
                 'drishti_location_view.xml',
                 'request_product_view.xml',
                 'wizard/request_product_merge_view.xml',
                 'location_sequence.xml',
                 'purchase_requisition_view.xml',
                 'wizard/purchase_requisition_merge_view.xml',
                 'job_order_view.xml',
                 'drishti_location_data.xml',
                 'job_order_dept_sequence.xml',
            
            
                 ],
    'demo': [],
    'test': [  
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'css': [  ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
