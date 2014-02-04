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


from osv import fields, osv
from tools.translate import _
import StringIO
import cStringIO
import base64
import xlrd
import string
import calendar
from calendar import monthrange
import datetime

class attendance_import(osv.osv_memory):
    _name='attendance.import'
    _columns={
              'file':fields.binary("File Path:"),
              'file_name':fields.char('File Name:'),
              'location':fields.selection([('1', 'Branch1'), ('2', 'Branch2')],'Location',required=True),
              }
    def import_attendance(self,cr,uid,ids,context=None):

        cur_obj = self.browse(cr,uid,ids)[0]
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        date_dict = {}
        if cur_obj.location == '1':
            date_from1 = sheet.row_values(0,0,sheet.ncols)[3] 
            
            from_date = int(date_from1[:2])
            month = int(date_from1[3:5])
            year = int(date_from1[6:10])
            date_from = datetime.date(year, month, 1)
            date_to = datetime.date(year, month, calendar.monthrange(year, month)[1])
            i = 0
            for p in range(1,calendar.monthrange(year, month)[1]+1):
                   date_dict[p] = datetime.date(year,month ,p)
            while i < sheet.nrows:
              emp_code1 =sheet.row_values(i,0,sheet.ncols)[0]
              emp_name =sheet.row_values(i,0,sheet.ncols)[1]
              emp_code = '0'* (4-len(str(int(emp_code1)))) + str(int(emp_code1))
              employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
              if not employee_id:
                  i += calendar.monthrange(year, month)[1]
              else:
                  employee_id = employee_id[0]
                  emp_obj =   self.pool.get('hr.employee').browse(cr,uid,employee_id) 
                  attendance_id = self.pool.get('hr.attendance.table').create(cr,uid,{'employee_id': employee_id,'date_from' : date_from,'date_to' : date_to})
                  contract_ids = self.pool.get('hr.payslip').get_contract( cr, uid, emp_obj, date_from, date_to, context=None)
                  if not contract_ids:
                        raise osv.except_osv(('Warning !'),_('The Contract does not exist!'))
                        
                  contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context) and self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context)[0] or False 
                  
                  for d in range(1,calendar.monthrange(year, month)[1]+1):
                        j = sheet.row_values(i,0,sheet.ncols)[7]
                        absent_info = ''
                        final_result = ''
                        if contract_obj:
                            search_for_weekly_off = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract_obj.working_hours, date_dict[d], context)
                            search_for_even_saturday = self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date_dict[d]),('type','=','even_sat')])
                            search_for_holiday=self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date_dict[d]),('type','<>','even_sat')])
                            search_for_leave=self.pool.get('hr.holidays').search(cr, uid, [('employee_id','=',employee_id),('state','=','validate'),('type','=','remove'),('date_from','<=',date_dict[d].strftime('%Y-%m-%d')),('date_to','>=',date_dict[d].strftime('%Y-%m-%d'))])
                            if search_for_even_saturday:
                                search_for_weekly_off = 0.0
                            if search_for_leave:  
                                      absent_info = self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.payroll_code.name or self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.name
                                      if  absent_info == "Unpaid":
                                          absent_info = 'UL'
                                      else:
                                          absent_info = 'PL'
                            elif search_for_holiday:
                                    absent_info = 'H'
                            elif not search_for_weekly_off:
                                absent_info = 'WO'
                        if absent_info:
                            if j== 'P' and absent_info=='H': 
                                final_result = 'HH'                
                            else:
                                 final_result = absent_info       
                        else:
                            if j== 'P':        
                                        final_result ='P'
                            else:
                                       final_result ='A'  
                        if j == 'P':
                           attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                                  'date' : date_dict[d],'attendance_table':attendance_id,
                                  'attendance':True,'absent_info':absent_info,'final_result':final_result})
                        else:
                           attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                                  'date' : date_dict[d],'attendance_table':attendance_id,
                                  'absent_info':absent_info,'final_result':final_result})   
                        i += 1
                        
        else:
                
            #date_from1 = sheet.row_values(5,0,sheet.ncols)[6] 
            #date_to1 = sheet.row_values(5,0,sheet.ncols)[13] 
            from_date = 1 #int(date_from1[:2])
            month = 9 #int(date_from1[3:5])
            year = 2013 #int(date_from1[6:10])
            to_date = 30 #int(date_to1[:2])
             
            
            
            
            for i in range(1,to_date+1):
                    
                   date_dict[i] = datetime.date(year,month ,i)
                   
            date_from = datetime.date(year, month, 1)
            date_to = datetime.date(year, month, to_date)
             
            
            for i in range(1,sheet.nrows):
              emp_code =sheet.row_values(i,0,sheet.ncols)[1]
              emp_name =sheet.row_values(i,0,sheet.ncols)[2]
              employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
              if employee_id:
                    
                employee_id = employee_id[0]
                emp_obj =   self.pool.get('hr.employee').browse(cr,uid,employee_id)
                 
                     
                attendance_id = self.pool.get('hr.attendance.table').create(cr,uid,{'employee_id': employee_id,'date_from' : date_from,'date_to' : date_to})
                d =1
    
     
                
                
                
        
                contract_ids = self.pool.get('hr.payslip').get_contract( cr, uid, emp_obj, date_from, date_to, context=None)
                
                if  contract_ids:
                
                  contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context) and self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context)[0] or False
                     
                  for j in sheet.row_values(i,5,monthrange(year, month)[1]+5):
                    absent_info = ''
                    final_result = ''
                    if contract_obj:
                        search_for_weekly_off = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract_obj.working_hours, date_dict[d], context)
                         
                        search_for_even_saturday = self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date_dict[d]),('type','=','even_sat')])
                        
                        search_for_holiday=self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date_dict[d])])
                        
                        
                        search_for_leave=self.pool.get('hr.holidays').search(cr, uid, [('employee_id','=',employee_id),('state','=','validate'),('type','=','remove'),('date_from','<=',date_dict[d].strftime('%Y-%m-%d')),('date_to','>=',date_dict[d].strftime('%Y-%m-%d'))])
                        
                         
                        if search_for_even_saturday:
                            search_for_weekly_off = 0.0
                        
                        if search_for_leave:  
                                  absent_info = self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.payroll_code.name or self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.name
                                  
                                  if  absent_info == "Unpaid":
                                      absent_info = 'UL'
                                  else:
                                      absent_info = 'PL'
                        elif search_for_holiday:
                                
                                absent_info = 'H'
                            
                    if absent_info:
                        if j== 'P' and absent_info=='H': 
                             final_result = 'HH'   
                                 
                                      
                        else:
                             final_result = absent_info       
                    else:
                        if j== 'P':        
                                    final_result ='P'
                        else:
                            if j== 'C':
                                    absent_info='Compensatory-Off'
                                    final_result='WO'
                            if j== 'W':
                                    absent_info='WO'
                                    final_result='WO'
                            if j== 'L':
                                    absent_info='L'
                                    final_result='PL'
                            if j== 'U':
                                    absent_info='UL'
                                    final_result='UL'
#                             if j== 'H':
#                                     absent_info='H'
#                                     final_result='H'
                            if j== 'O':
                                    absent_info='Work at other Location'
                                    final_result='P'
                            if j== 'A':
                                   absent_info='A'
                                   final_result ='A'  
                    if j== 'P':
                       attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'attendance':True,'absent_info':absent_info,'final_result':final_result})
                    else:
                        
                       attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':absent_info,'final_result':final_result})   
                    d +=1
                   
        return True
    
attendance_import()
