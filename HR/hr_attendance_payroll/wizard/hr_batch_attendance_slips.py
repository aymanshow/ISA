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
from datetime import datetime
from dateutil import relativedelta

from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_batch_attendance_slips(osv.osv_memory):

    _name ='hr.batch.attendance.slips'
    _description = 'Generate Batch Attendance Slips for all Selected Employees'
    _columns = {
        'employee_ids': fields.many2many('hr.employee', 'hr_employee_batch_rel', 'batch_id', 'employee_id', 'Employees'),
        'notes':fields.text('List of Employees who have completed 1 year of Service'),
        'user':fields.many2one('res.users','Recepient User'),
    }
    
    
    def compute_sheet(self, cr, uid, ids, context=None):
         
         emp_pool = self.pool.get('hr.employee')
         run_pool = self.pool.get('attendance.batch')
         slip_pool = self.pool.get('hr.attendance.table')
         slip_line_pool = self.pool.get('hr.attendance.table.line')
         data = self.read(cr, uid, ids, context=context)[0]
         if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate batch attendance slip(s)."))
         if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, context['active_id'], ['date_from', 'date_to'])
            from_date1 =  run_data.get('date_from', False)
            to_date1 = run_data.get('date_to', False)
            form_id = run_data.get('id', False)
            
         for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
             print emp.id, "SELECTED EMPLOYEE IDS"
             search_attendance_id = self.pool.get('hr.attendance.table').search(cr, uid, [('employee_id','=', emp.id),('date_from','=', from_date1),('date_to','=',to_date1)])
             print search_attendance_id, "SEARCH ATTENDANCE ID"
             attendance_id = self.pool.get('hr.attendance.table').create(cr, uid, {'employee_id': emp.id, 'date_from': from_date1, 'date_to': to_date1, 'batch_attendance_id': form_id})
             
             self.pool.get('hr.attendance.table').generate_attendance(cr,uid,[attendance_id],context=None)
             
         return True

hr_batch_attendance_slips()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
