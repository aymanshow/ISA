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
    
#     def send_one_year_mail(self, cr, uid, ids, context=None):
#          print "%%%%%%%%%%%%%%%%%%% THE REQUIRED ID %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%", ids
#          print "jjjjjjjjjjjjjjjjjjjjjjjjjj Send 1 year Mail Scheduler jjjjjjjjjjjjjjjjjjjjjjjjjjj"
#          search_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','>',0)])
#          print search_emp_record, "*********************************ALL EMPLOYEE RECORDS***************************************"
#             
#             
#          #for l in self.pool.get('hr.employee').browse(cr,uid,search_emp_record):
#          #list_items = list(range(16,21))
#          #print list_items, "******************* This is a List ****************************"    
#          #search_emp_records = self.pool.get('hr.employee').search(cr, uid, [('id','in',list_items)])
#          #print search_emp_record, "mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm"
#          
#          list_of_emp = []
#          
#          for d in self.pool.get('hr.employee').browse(cr, uid, search_emp_record):
#              emp_joining_date = d.joining_date
#              work_status = d.work_status
#              
#              from time import strftime
#              current_date = strftime("%Y-%m-%d")
#             
#              print emp_joining_date, "uuuuuuuuuuuuuuuuuuu EMPLOYEE JOINING DATE uuuuuuuuuuuuuuuuuuuuuuuuuu"
#              print current_date, "uuuuuuuuuuuuuuuuuuu EMPLOYEE CURRENT DATE uuuuuuuuuuuuuuuuuuuuuuuuuu"
#             
#              from datetime import datetime
#              today_date = datetime.strptime(current_date,"%Y-%m-%d")
#              emp_joining_date = datetime.strptime(d.joining_date,"%Y-%m-%d")
#             
#              months_difference = self.pool.get('hr.employee').diff_month(cr,uid,ids,today_date,emp_joining_date) 
#             
#              print months_difference, "pppppppppppppppp MONTHS DIFFERENCE pppppppppppppppppppppppppppppp"
#              print d.id, "ttttttttttttttttttt EMPLOYEE ID ttttttttttttttttttttttttttttttttttttt"
#              
#              self.pool.get('hr.employee').write(cr, uid, d.id, {'no_of_months_worked':months_difference})
#              
#              
#              
#              if (months_difference == 12 and work_status == 'Temperory'):
#                  
#                     list_of_emp.append(d.name)
#                     #print names_of_emp, "hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"
#         
#                     #self.write{cr, }
# #                     email_template_obj = self.pool.get('email.template')
# #                                                  
# #                     template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.employee')], context=context)
# #                     print template_ids, "nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn"
# #                     
# #                     if template_ids:                                  
# #                         mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], d.id, force_send=True, context=context)
#          print list_of_emp, "gggggggggggggggggggg LIST OF EMPLOYEES gggggggggggggggggggggggg" 
#          names_of_emp = list_of_emp
#          print names_of_emp, "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"
#          search_group = self.pool.get('res.groups').search(cr,uid,[('name','=','Officer')])
#          print search_group[0], "^^^^^^^^^^^^^^^^^^^^^^^^HR OFFICERS GROUP^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
#          cr.execute("select uid from res_groups_users_rel where gid = %(val)s",{'val':search_group[0]})
#          user_id = cr.fetchall()[1]
#          print user_id, "iiiiiiiiiiiiiiiiiiiii Appropriate User ID iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"
#          
#          #search_user = self.pool.get('res.groups.users.rel').search(cr,uid,[('gid','=',search_group[0])])
#          #print search_user, "{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}"
#          
# # -----------------------------Past Important Code---------------------------------------         
#          self.write(cr, uid, ids, {'notes':names_of_emp, 'user':user_id})
#          email_template_obj = self.pool.get('email.template')
#                                                  
#          template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.batch.attendance.slips')], context=context)
#          print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn"
#         
#          if template_ids:                                  
#             mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], ids, force_send=True, context=context)
#             
# # ----------------------------Past Important Code-------------------------------------------
# 
#          search_user_id = self.pool.get('res.users').search(cr, uid, [('id','=',user_id)])
#          print search_user_id, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 
# 
# 
# #          for h in self.pool.get('hr.employee').browse(cr,uid,list_of_emp):
# #              for t in list_of_emp:
# #                  print t, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
# #                  self.write(cr, uid, ids, {'notes':t})
# 
#          return True
    
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
