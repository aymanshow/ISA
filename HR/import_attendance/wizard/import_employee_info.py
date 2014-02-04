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
    _inherit='attendance.import'
    
    def import_employees(self,cr,uid,ids,context=None):

        cur_obj = self.browse(cr,uid,ids)[0]
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        
        for i in range(1,sheet.nrows):
            
            emp_name =sheet.row_values(i,0,sheet.ncols)[0]
           
            emp_designation =sheet.row_values(i,0,sheet.ncols)[1]
            
            employee_id = self.pool.get('hr.employee').search(cr,uid,[('name','=',emp_name)])
            
            
            position = self.pool.get('hr.job').search(cr,uid,[('name','=',emp_designation)])
            
            for jl in self.pool.get('hr.job').browse(cr,uid,position):
                position=jl.id
                
            if not position:
                position= self.pool.get('hr.job').create(cr,uid,{'name': emp_designation})
                
                
                
            from time import strftime
            today_date = strftime("%Y-%m-%d")
            if not employee_id:
                
                
                 
            	employee_id = self.pool.get('hr.employee').create(cr,uid,{'name':emp_name, 'job_id':position, 'joining_date': today_date})
                
        return True
    
    def import_payment_info(self,cr,uid,ids,context=None):

        cur_obj = self.browse(cr,uid,ids)[0]
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        
        for i in range(1,sheet.nrows):
            emp_code =sheet.row_values(i,0,sheet.ncols)[0]
            emp_wage =sheet.row_values(i,0,sheet.ncols)[6]
            emp_level =sheet.row_values(i,0,sheet.ncols)[5]
            salary_structure =sheet.row_values(i,0,sheet.ncols)[8]
            working_schedule =sheet.row_values(i,0,sheet.ncols)[7]
            employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
            
            for el in self.pool.get('hr.employee').browse(cr,uid,employee_id):
                emp_number=el.id
                emp_name=el.name
                
                
                
            structure_id = self.pool.get('hr.payroll.structure').search(cr,uid,[('name','=',salary_structure)])
            
            for sl in self.pool.get('hr.payroll.structure').browse(cr,uid,structure_id):
                structure_number=sl.id
                
                
                
            level_id = self.pool.get('employee.level').search(cr,uid,[('name','=',emp_level)])

            for ml in self.pool.get('employee.level').browse(cr,uid,level_id):
                level_number=ml.id
                
            schedule_id = self.pool.get('resource.calendar').search(cr,uid,[('name','=',working_schedule)])
            
            for wl in self.pool.get('resource.calendar').browse(cr,uid,schedule_id):
                schedule_number=wl.id
                    
                
            contract_id = self.pool.get('hr.contract').search(cr,uid,[('name','=',emp_name)])
            
            if not contract_id:
                
            
                new_contract = self.pool.get('hr.contract').create(cr,uid,{'name' : emp_name,'employee_id' : emp_number,'wage': emp_wage, 'struct_id': structure_number,'working_hours': schedule_number,'level_ids': level_number})

            else:
                for kl in self.pool.get('hr.contract').browse(cr,uid,contract_id):          
                    self.pool.get('hr.contract').write(cr,uid,kl.id,{'working_hours': schedule_number,'struct_id':structure_number,'wage':emp_wage,'level_ids':level_number})

                        
        return True

    def update_category_info(self,cr,uid,ids,context=None):

        cur_obj = self.browse(cr,uid,ids)[0]
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        
        for i in range(1,sheet.nrows):
            emp_code =sheet.row_values(i,0,sheet.ncols)[1]
            emp_category =sheet.row_values(i,0,sheet.ncols)[3]
   
        
            emp_tag = self.pool.get('hr.employee.category').search(cr,uid,[('name','=',emp_category)])
            
            for tl in self.pool.get('hr.employee.category').browse(cr,uid,emp_tag):
                tag_id=tl.id
                
            if not emp_tag:
                tag_id= self.pool.get('hr.employee.category').create(cr,uid,{'name': emp_category})
                  
              
            employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
            
            for el in self.pool.get('hr.employee').browse(cr,uid,employee_id):          
                self.pool.get('hr.employee').write(cr,uid,el.id,{'category': tag_id})
                emp_category_no=el.category.id
                
                if emp_category_no==9:
                   self.pool.get('hr.employee').write(cr,uid,el.id,{'active': False}) 

        return True
    
    def import_mobile_arrears(self,cr,uid,ids,context=None):
        
        cur_obj = self.browse(cr,uid,ids)[0]
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        
        for i in range(1,sheet.nrows):
            emp_code =sheet.row_values(i,0,sheet.ncols)[0]
            mobile =sheet.row_values(i,0,sheet.ncols)[1]
            arrears =sheet.row_values(i,0,sheet.ncols)[2]
            
            
            
            emp_code = 'SLSG-' + str(emp_code)
            
            employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
            
            
            for el in self.pool.get('hr.employee').browse(cr,uid,employee_id):
                emp_number=el.id
                
                
            
            payslip_id = self.pool.get('hr.payslip').search(cr,uid,[('employee_id','=',emp_number),('date_from','=','2013-09-01'),('date_to','=','2013-09-30')])
            
            
            for x in self.pool.get('hr.payslip').browse(cr, uid, payslip_id):
                 payslip_form_id=x.id
                 
                 
                 
                 input_payslip_id_mobile= self.pool.get('hr.payslip.input').search(cr,uid,[('payslip_id','=',payslip_form_id),('name','=','Mobile Deduction')])
                 
                 for y in self.pool.get('hr.payslip.input').browse(cr, uid, input_payslip_id_mobile):
                     input_id_mobile=y.id
                     
                     self.pool.get('hr.payslip.input').write(cr,uid,y.id,{'amount':mobile})
                     
                 input_payslip_id_arrears= self.pool.get('hr.payslip.input').search(cr,uid,[('payslip_id','=',payslip_form_id),('name','=','Arrears')])
                 
                 for k in self.pool.get('hr.payslip.input').browse(cr, uid, input_payslip_id_arrears):
                     input_id_arrears=k.id
                     
                     self.pool.get('hr.payslip.input').write(cr,uid,k.id,{'amount':arrears})    
                     
                 payslip_template_obj = self.pool.get('hr.payslip')
            
                 payroll_id = payslip_template_obj.compute_sheet(cr, uid, payslip_id, context=context)
                
                     
                 
    
