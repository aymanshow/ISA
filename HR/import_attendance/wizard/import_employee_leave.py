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
                
                
                         dic = {}
                         if j == 'P': 
                              attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'attendance':True,'absent_info':'', 'final_result':'P'})
                         if j == 'L': 
                             attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':'PL', 'final_result':'PL'})
                         elif j == 'U':
                             attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id,
                              'date' : date_dict[d],'attendance_table':attendance_id,
                              'absent_info':'UL', 'final_result':'UL'})
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
                             
 
     
                         elif j == 'W':
                             dic ={
                                   'absent_info':'WO',
                                   'final_result':'WO' ,
                                   }
                d += 1          
            self.pool.get('hr.holidays').holidays_validate(cr, uid, holiday_list)
            
            
                
            
                          
                          
                          
            

    
