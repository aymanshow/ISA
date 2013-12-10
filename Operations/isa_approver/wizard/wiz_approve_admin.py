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
from openerp.tools.translate import _

class wiz_approve_by_admin(osv.osv_memory):
    _name = "wiz.approve.by.admin"
    _description = "Approve by Admin"
    _columns = {
        'select_for_approve':fields.selection
        }
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(wiz_approve_by_admin, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            tomerge = set([int(context['active_id'])])
            hold = self.pool.get('project.project').browse(cr, uid, int(context['active_id']), context=context)
            res.update({'wiz_datas_fname' : hold.datas_fname,})
        return res

wiz_approve_by_admin()
