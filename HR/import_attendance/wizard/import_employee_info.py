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
            emp_code =sheet.row_values(i,0,sheet.ncols)[1]
            emp_ssn_no =sheet.row_values(i,0,sheet.ncols)[2]
            
            
            #tag =sheet.row_values(i,0,sheet.ncols)[3]
            emp_designation =sheet.row_values(i,0,sheet.ncols)[3]
            emp_department =sheet.row_values(i,0,sheet.ncols)[4]
            related_user =sheet.row_values(i,0,sheet.ncols)[5]
            country =sheet.row_values(i,0,sheet.ncols)[6]
#             emp_epf_no =sheet.row_values(i,0,sheet.ncols)[6]
#             if type(emp_epf_no) ==type(1.0):
#                 emp_epf_no = (emp_epf_no)
#             a =sheet.row_values(i,0,sheet.ncols)[7]
#             if type(a) ==type(1.0):
#                 a = (a)
#             b =sheet.row_values(i,0,sheet.ncols)[8]
#             if type(b) ==type(1.0):
#                 b = (b)
#             reason_for_leaving =sheet.row_values(i,0,sheet.ncols)[10]
#             dt_of_joining =sheet.row_values(i,0,sheet.ncols)[11]
#             dt_of_birth =sheet.row_values(i,0,sheet.ncols)[12]
#             father_name =sheet.row_values(i,0,sheet.ncols)[14]
#             pincode =sheet.row_values(i,0,sheet.ncols)[18]
#             if type(pincode) ==type(1.0):
#                 pincode = (pincode)
#             mobile_no =sheet.row_values(i,0,sheet.ncols)[19]
#             if type(mobile_no) ==type(1.0):
#                 mobile_no = (mobile_no)
#                 print mobile_no, "22222222222222222222222222222222222222222"
#             telephone_no =sheet.row_values(i,0,sheet.ncols)[48]
#             if type(telephone_no) ==type(1.0):
#                 telephone_no = (telephone_no)
#             emergency_no =sheet.row_values(i,0,sheet.ncols)[47]
#             if type(emergency_no) ==type(1.0):
#                 emergency_no = (emergency_no)
#             gender =sheet.row_values(i,0,sheet.ncols)[44]
#             country =sheet.row_values(i,0,sheet.ncols)[63]
#             bank_name =sheet.row_values(i,0,sheet.ncols)[98]
#             branch_name=sheet.row_values(i,0,sheet.ncols)[99]
#             bank_code=sheet.row_values(i,0,sheet.ncols)[100]
#             company_name=sheet.row_values(i,0,sheet.ncols)[101]
# 
#             blood_group =sheet.row_values(i,0,sheet.ncols)[21]
#             active =sheet.row_values(i,0,sheet.ncols)[37]
#             import datetime
            employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
            
            
            position = self.pool.get('hr.job').search(cr,uid,[('name','=',emp_designation)])
            
            for jl in self.pool.get('hr.job').browse(cr,uid,position):
                position=jl.id
                
            if not position:
                position= self.pool.get('hr.job').create(cr,uid,{'name': emp_designation})
                
                
#             emp_tag = self.pool.get('hr.employee.category').search(cr,uid,[('name','=',tag)])
#             
#             for tl in self.pool.get('hr.employee.category').browse(cr,uid,emp_tag):
#                 tag_id=tl.id
#                 
#             if not emp_tag:
#                 tag_id= self.pool.get('hr.employee.category').create(cr,uid,{'name': tag})
#                     
#                 
            department = self.pool.get('hr.department').search(cr,uid,[('name','=',emp_department)])
             
            for pl in self.pool.get('hr.department').browse(cr,uid,department):
                department=pl.id
                 
            if not department:
                department= self.pool.get('hr.department').create(cr,uid,{'name': emp_department})
                 
                 
            country_number = self.pool.get('res.country').search(cr,uid,[('name','=',country)])
             
            for cl in self.pool.get('res.country').browse(cr,uid,country_number):
                country_number=cl.id
                
                
            user_number = self.pool.get('res.users').search(cr,uid,[('name','=', related_user)])
             
            for rl in self.pool.get('res.users').browse(cr,uid,user_number):
                user_number=rl.id
#                 
#                 
#             bank = self.pool.get('res.bank').search(cr,uid,[('name','=',bank_name)])
#             
#             for bl in self.pool.get('res.bank').browse(cr,uid,bank):
#                 bank_number=bl.id
#                 
#             if not bank:
#                 bank_number= self.pool.get('res.bank').create(cr,uid,{'name': bank_name})
#                 
#                 
#             company = self.pool.get('res.company').search(cr,uid,[('name','=',company_name)])
#             
#             for yl in self.pool.get('res.company').browse(cr,uid,company):
#                 company_number=yl.id
#                 
#             if not company:
#                 company_number= self.pool.get('res.company').create(cr,uid,{'name': company_name})
                
            from time import strftime
            today_date = strftime("%Y-%m-%d")
            if not employee_id:
                
                
                 
                employee_id = self.pool.get('hr.employee').create(cr,uid,{'identification_id': emp_code,'name':emp_name, 'job_id':position, 'ssnid': emp_ssn_no, 'joining_date': today_date})
                
            else:
                for tl in self.pool.get('hr.employee').browse(cr,uid,employee_id):          
                    self.pool.get('hr.employee').write(cr,uid,tl.id,{'department_id': department, 'country_id': country_number, 'user_id': user_number})
            emp_obj =   self.pool.get('hr.employee').browse(cr,uid,employee_id) 
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
#             nutritional_allowance =sheet.row_values(i,0,sheet.ncols)[4]
#             att_inc_allowance =sheet.row_values(i,0,sheet.ncols)[5]
#             holidays_calendar =sheet.row_values(i,0,sheet.ncols)[6]
            working_schedule =sheet.row_values(i,0,sheet.ncols)[7]
#             contract_start_date =sheet.row_values(i,0,sheet.ncols)[8]
#             da_lta_fa =sheet.row_values(i,0,sheet.ncols)[9]
#             house_rent_allowance =sheet.row_values(i,0,sheet.ncols)[10]
            #special_allowance =sheet.row_values(i,0,sheet.ncols)[11]
            
#             import datetime
#             date_start = datetime.datetime.strptime(contract_start_date, "%d/%m/%Y")
            
            
        
            #emp_code = 'SLSG-' + str(emp_code)
            
            
            employee_id = self.pool.get('hr.employee').search(cr,uid,[('identification_id','=',emp_code)])
            
            for el in self.pool.get('hr.employee').browse(cr,uid,employee_id):
                emp_number=el.id
                emp_name=el.name
                print emp_name, "lllllllllllllllllllllllllllllllllllll"
                
                
            structure_id = self.pool.get('hr.payroll.structure').search(cr,uid,[('name','=',salary_structure)])
            print salary_structure, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
            print structure_id, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
            for sl in self.pool.get('hr.payroll.structure').browse(cr,uid,structure_id):
                structure_number=sl.id
                
                
#             calendar_id = self.pool.get('holidays.calendar').search(cr,uid,[('name','=',holidays_calendar)])
#             
#             for tl in self.pool.get('holidays.calendar').browse(cr,uid,calendar_id):
#                 calendar_number=tl.id
                
            level_id = self.pool.get('employee.level').search(cr,uid,[('name','=',emp_level)])

            for ml in self.pool.get('employee.level').browse(cr,uid,level_id):
                level_number=ml.id
                
            schedule_id = self.pool.get('resource.calendar').search(cr,uid,[('name','=',working_schedule)])
            
            for wl in self.pool.get('resource.calendar').browse(cr,uid,schedule_id):
                schedule_number=wl.id
                    
                
            contract_id = self.pool.get('hr.contract').search(cr,uid,[('name','=',emp_name)])
            
            if not contract_id:
                
            
#             old_contract_id= self.pool.get('hr.contract').search(cr,uid,[('name','=',emp_name),('employee_id','=',emp_number),('date_end','=','2013-08-31')])
#             for old_contract in self.pool.get('hr.contract').browse(cr,uid,old_contract_id):
#                 old_struct_id=old_contract.struct_id.id
#                 print old_struct_id, "1111111111111111111111111111111111111111111111"
            
                
                #new_contract = self.pool.get('hr.contract').create(cr,uid,{'name' : emp_name,'employee_id' : emp_number,'wage': emp_wage, 'struct_id': old_struct_id, 'nutritional_allowance': nutritional_allowance,  'attendance_incentive': att_inc_allowance, 'holidays_id': calendar_number, 'working_hours': schedule_number, 'date_start': date_start, 'da_lta_fa': da_lta_fa, 'hra': house_rent_allowance, 'level_ids': level_number})
                new_contract = self.pool.get('hr.contract').create(cr,uid,{'name' : emp_name,'employee_id' : emp_number,'wage': emp_wage, 'struct_id': structure_number,'working_hours': schedule_number,'level_ids': level_number})
                #self.pool.get('hr.contract').on_change_wage_level(cr,uid,contract_id,emp_wage,context=context)
            else:
                for kl in self.pool.get('hr.contract').browse(cr,uid,contract_id):          
                    self.pool.get('hr.contract').write(cr,uid,kl.id,{'working_hours': schedule_number,'struct_id':structure_number,'wage':emp_wage,'level_ids':level_number})
                    #self.pool.get('hr.contract').on_change_wage_level(cr,uid,contract_id,emp_wage,context=context)
                        
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
                print emp_number, "EMP NUMBER &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&"
                
            
            payslip_id = self.pool.get('hr.payslip').search(cr,uid,[('employee_id','=',emp_number),('date_from','=','2013-09-01'),('date_to','=','2013-09-30')])
            
            
            for x in self.pool.get('hr.payslip').browse(cr, uid, payslip_id):
                 payslip_form_id=x.id
                 print payslip_form_id, "555555555555555555555555555"
                 
                 
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
                
                     
                 #if not input_payslip_id:
                 #   input_payslip_id= self.pool.get('hr.payslip.input').create(cr,uid,{'payslip_id': payslip_id, 'code': 'MO', 'name': 'Mobile Deduction', 'amount': mobile  })      
                                                                                    
                     
                     
#             emp_wage =sheet.row_values(i,0,sheet.ncols)[2]
#             salary_structure =sheet.row_values(i,0,sheet.ncols)[3]
#             nutritional_allowance =sheet.row_values(i,0,sheet.ncols)[4]

        
# class hr_payslip_run(osv.osv):
#     _inherit = "hr.payslip.run"
#     
#     def contracts_renewal(self,cr,uid,ids,context=None):
#         
#         return {
#             'name':"Importing Arrears",
#             'view_mode': 'form',
#             'view_id': False,
#             'view_type': 'form',
#             'res_model': 'attendance.import',
#             'res_id': '',
#             'type': 'ir.actions.act_window',
#             'nodestroy': True,
#             'target': 'new',
#             'domain': '[]',
#             #'context': default_context,
#          }
# hr_payslip_run()    

    
