from osv import fields, osv
from tools.translate import _
import StringIO
import cStringIO
import base64
import xlrd
import string
import calendar
import datetime
from calendar import monthrange

class attendance_import(osv.osv_memory):
    _inherit='attendance.import'
    
    def import_leave(self,cr,uid,ids,context=None):

        cur_obj = self.browse(cr,uid,ids)[0]
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        
        date_dict = {}
        #date_from1 = sheet.row_values(5,0,sheet.ncols)[6] 
        #date_to1 = sheet.row_values(5,0,sheet.ncols)[13] 
        from_date = 1 #int(date_from1[:2])
        month = 8 #int(date_from1[3:5])
        year = 2013 #int(date_from1[6:10])
        to_date = 31 # int(date_to1[:2])
         
        
        
        for i in range(1,to_date+1):
               date_dict[i] = datetime.date(year,month ,i)
        
        date_from = datetime.date(year, month, 1)
        date_to = datetime.date(year, month, to_date)
         
        
        for i in range(1,sheet.nrows):
           emp_code =sheet.row_values(i,0,sheet.ncols)[1]
           emp_name =sheet.row_values(i,0,sheet.ncols)[2]
           employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
           if  employee_id:  
            employee_id = employee_id[0]
            
            attendance_id = self.pool.get('hr.attendance.table').create(cr,uid,{'employee_id': employee_id,'date_from' : date_from,'date_to' : date_to})
            print attendance_id, "ATTENDANCE_ID"
            d =1
            holiday_list = []
            
            for j in sheet.row_values(i,3,monthrange(year, month)[1]+3):
                
                
                if j:
#                   status_id  = self.pool.get('hr.holidays.status').search(cr, uid, [('leave_code','=',j)]) 
#                   
#                   if status_id:
#                       holiday_ids = self.pool.get('hr.holidays').search(cr,uid,[('employee_id','=',employee_id),
#                                                                   ('date_to','=',(date_dict[d]-datetime.timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')),
#                                                                   ('holiday_status_id','=',status_id[0])])
#                       
#                       if holiday_ids:
#                           leave_obj = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids[0])
#                           days = leave_obj.number_of_days_temp
#                           
#                           self.pool.get('hr.holidays').write(cr, uid, holiday_ids,{'date_to':date_dict[d]+ datetime.timedelta(seconds=3600*24-1),
#                                                                                     'number_of_days_temp' : days +1},)
#                                                                  
#                       else:    
#                           
#                           dic = {
#                                  'employee_id': employee_id,
#                                  'date_from': date_dict[d],
#                                  'date_to': date_dict[d]+ datetime.timedelta(seconds=3600*24-1)  ,
#                                  'holiday_status_id': status_id[0],
#                                  'number_of_days_temp' :1
#                                  }
#                           
#                           holiday_id = self.pool.get('hr.holidays').create(cr, uid, dic)
#                           
#                           holiday_list.append(holiday_id)
                          
                  #if attendance_id:
                   #      att_line_id = self.pool.get('hr.attendance.table.line').search(cr ,uid,
                    #                                                          [('attendance_table','=',attendance_id[0]),
                     #                                                          ('date','=', date_dict[d])])
                          
                         dic = {}
                         if j == 'P': 
                              attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'attendance':True,'absent_info':'', 'final_result':'P'})
#                              dic ={
#                                    'absent_info':'',
#                                    'final_result':'P' ,
#                                    }
                         if j == 'L': 
                             attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':'PL', 'final_result':'PL'})
#                              dic ={
#                                    'absent_info':'L',
#                                    'final_result':'PL' ,
#                                    }
                         elif j == 'U':
                             attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':'UL', 'final_result':'UL'})
#                              dic ={
#                                    'absent_info':'UL',
#                                    'final_result':'UL' ,
#                                    }
                         elif j == 'O':
                             attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':'Work at other Location', 'final_result':'P'})
                         elif j == 'C':
                             attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':'Compensatory Off', 'final_result':'P'})
                         elif j == 'T':
                             dic ={
                                   'absent_info':'Mobile Attendance',
                                   'final_result':'P' ,
                                   }
                         elif j == 'H':
                             dic ={
                                   'absent_info':'Holiday',
                                   'final_result':'P' ,
                                   }    
                         elif j == 'M':
                             dic ={
                                   'absent_info':'Manual Attendance',
                                   'final_result':'P' ,
                                   }
                             
#                              for x in self.pool.get('hr.attendance.table.line').browse(cr, uid, att_line_id):
#                                  emp_name=x.employee_id.id
#                                  date=x.date
#                                  attendance=x.attendance
#                                  emp_contract_search=self.pool.get('hr.contract').search(cr, uid, [('employee_id','=',emp_name)])
#                                  for c in self.pool.get('hr.contract').browse(cr,uid,emp_contract_search):
#                                      holidays_calendar=c.holidays_id.id
#                                  emp_categ_search=self.pool.get('hr.employee').search(cr, uid, [('id','=',emp_name)])
#                                  for p in self.pool.get('hr.employee').browse(cr,uid,emp_categ_search):
#                                      category=p.category.id
#                                      category_name=p.category.name
#                                      if category_name=='North Goa' or 'South Goa':
#                                          leaves_search=self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',holidays_calendar),('date_from','=',date)])
#                                          if leaves_search: 
#                                              dic ={
#                                                     'absent_info':'Manual Attendance',
#                                                     'final_result':'HH' ,
#                                                     }            
 
     
                         elif j == 'W':
                             #line_obj = self.pool.get('hr.attendance.table.line').browse(cr, uid, att_line_id[0])
                             #print line_obj, "Line Object"
                             dic ={
                                   'absent_info':'WO',
                                   'final_result':'WO' ,
                                   }
#                              for x in self.pool.get('hr.attendance.table.line').browse(cr, uid, att_line_id):
#                                  emp_name=x.employee_id.id
#                                  date=x.date
#                                  attendance=x.attendance
#                                  emp_contract_search=self.pool.get('hr.contract').search(cr, uid, [('employee_id','=',emp_name)])
#                                  for c in self.pool.get('hr.contract').browse(cr,uid,emp_contract_search):
#                                      holidays_calendar=c.holidays_id.id
#                                  emp_categ_search=self.pool.get('hr.employee').search(cr, uid, [('id','=',emp_name)])
#                                  for p in self.pool.get('hr.employee').browse(cr,uid,emp_categ_search):
#                                      category=p.category.id
#                                      category_name=p.category.name
#                                      if category_name=='North Goa' or 'South Goa':
#                                          leaves_search=self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',holidays_calendar),('date_from','=',date)])
#                                          if leaves_search: 
#                                              dic ={
#                                                     'absent_info':'WO',
#                                                     'final_result':'HH' ,
#                                                     }            
                             
                             
                             
                                      
                         #self.pool.get('hr.attendance.table.line').write(cr, uid, att_line_id, dic )
                         
#                          if j=='P':
#                              attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
#                               'date' : date_dict[d],'attendance_table':attendance_id,
#                               'attendance':True},dic)
#                          else:
#                              attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
#                               'date' : date_dict[d],'attendance_table':attendance_id},dic)
                             
                d += 1          
            self.pool.get('hr.holidays').holidays_validate(cr, uid, holiday_list)
            
            
                
            
                          
                          
                          
            

    