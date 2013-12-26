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
import time
from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _

class request_product_group(osv.osv_memory):
    _name = "request.product.group"
    _description = "Request Product Merge"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}
        res = super(request_product_group, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'request.product' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('Warning!'),
            _('Please select multiple request product to merge in the list view.'))
        return res
    
    def merge_request(self, cr, uid, ids, context=None):
        """
             To merge similar type of request product.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: request product view

        """
        request_obj = self.pool.get('request.product')
        
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        #result = mod_obj._get_id(cr, uid, 'drishti_location', 'view_purchase_order_filter')
        #id = mod_obj.read(cr, uid, result, ['res_id'])

        allorders = request_obj.do_merge(cr, uid, context.get('active_ids',[]), context)
        
        return True
    
        return {
            'domain': "[('id','in', [" + ','.join(map(str, allorders.keys())) + "])]",
            'name': _('Request Product'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'request.product',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': id['res_id']
        }

request_product_group()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
