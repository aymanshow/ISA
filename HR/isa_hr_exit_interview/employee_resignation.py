from osv import fields, osv
import datetime
from datetime import datetime, timedelta
import time
from tools.translate import _
import openerp.addons.decimal_precision as dp

class resign_information(osv.osv):
    _name = "resign.information"
    _description = "Resign Form"
    _columns = {
        'employee_id': fields.many2one('hr.employee','Employee', readonly=True),
        'designation_id':fields.many2one('hr.job','Designation',readonly=True),
        'department_id':fields.many2one('hr.department','Department',readonly=True),
        'resign_date':fields.date('Date of Resign',required=True),
        'reason':fields.text('Reason',required=True),
        'state': fields.selection([('draft','New'),
                                   ('initiate','Confirm Resignation'),
                                   ('approve', 'Approve'),
                                   ('exit_int','Exit interview'), 
                                   ('relieved', 'Relieved'),
                                   ('close','Closed')], 'Status', required=True,),
        'state1': fields.selection([('emp_successfully_relieved','Emp Successfully Relieved')],'State',readonly=True),
        'test_information_id':fields.one2many('resign.question','resign_ques_ids','Question'),
        'company_asset_id':fields.one2many('resign.company.asset','resign_com_asset_ids','Question'),
        'company_restriction_id':fields.one2many('resign.company.restriction','resign_com_restriction_ids','Question'),
        'final_exit_ques_id':fields.one2many('resign.final.exit.ques','final_resign_exit_ques_ids','Question'),
        'another_position':fields.boolean("Another Position"),
        'attendance':fields.boolean("Attendance"),
        'personal_reasons':fields.boolean("Personal Reasons"),
        'violation_of_company_policy':fields.boolean("Violation of Company Policy"),
        'relocation':fields.boolean("Relocation"),
        'lay_off':fields.boolean("Lay Off"),
        'retirement':fields.boolean("Retirement"),
        'reorganization':fields.boolean("Reorganization"),
        'return_to _school':fields.boolean("Return to School"),
        'position_eliminated':fields.boolean("Position Eliminated"),
        'other':fields.boolean("Other"),
        'other1':fields.boolean("Other"),
        'emp_comment':fields.text('Comment'),
        'interviewer_comment':fields.text('Comment'),
        
        'termination_date':fields.date('Termination Date'),
        'emp_id':fields.char('Employee Id'),
        'eligible_for_rehire':fields.boolean('Eligible for Rehire'),
        'job_code':fields.char('Job Code')

    }
    _defaults={
        'state':'draft'
    }
    def default_get(self, cr, uid, fields, context=None):
        res = super(resign_information, self).default_get(cr, uid, fields, context=context)
        emp_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not emp_id:
            raise osv.except_osv(_('Error!'), _('First create user as Employee!'))
        emp_obj = self.pool.get('hr.employee').browse(cr, uid, emp_id[0], context=context)
        res.update({'employee_id': emp_id[0],
                    'designation_id': emp_obj.job_id.id,
                    'department_id': emp_obj.department_id.id,
                    })
        return res
    
    def submit_resign(self,cr,uid,ids,context=None):
         self.write(cr, uid, ids, {'state': 'initiate'})
         return True
     
    def emp_exit_interview(self,cr,uid,ids,context=None):
         self.write(cr, uid, ids, {'state': 'exit_int'})
         return True
    def emp_releived(self,cr,uid,ids,context=None):
         self.write(cr, uid, ids, {'state': 'relieved'})
         self.write(cr, uid, ids, {'state1':'emp_successfully_relieved'})
         return True
    def emp_close(self,cr,uid,ids,context=None):
         self.write(cr, uid, ids, {'state': 'close'})
         return True
#    def emp_releived(self,cr,uid,ids,context=None):
#        self.write(cr, uid, ids, {'state':'successfully_relieved'})
#        return True
    
#    def create_data(self,cr,uid,rec,context=None):
#        dic = {'sr_no':rec.serial_number,
#                     'questions':rec.question,
#                     'resign_com_asset_ids': rec.id,
#                           }
#        return dic
#        
#    def admin_approve_resign(self,cr,uid,ids,context=None):
#         qus_id=self.pool.get('exit.interview.ques').search(cr,uid,[])
#         ques_obj=self.pool.get('exit.interview.ques').browse(cr,uid,qus_id[0])
#         obj=self.browse(cr,uid,ids[0])
#         list=[]
#         list1=[]
#         dic={}  
#         for val in ques_obj.company_property_id:
#              list.append(self.create_data(cr,uid,val))
#              print"--------------->>>",list
#         self.create(cr,uid,{'company_asset_id':list})              
#         self.write(cr, uid, ids[0], {'state': 'approve'})
#         return True 

    def admin_approve_resign(self,cr,uid,ids,context=None):
         qus_id=self.pool.get('exit.interview.ques').search(cr,uid,[])
         ques_obj=self.pool.get('exit.interview.ques').browse(cr,uid,qus_id[0])
         obj=self.browse(cr,uid,ids[0])
         list=[]
         list1=[]
         dic=dic1=dic2=dic3={}
         for val in ques_obj.question_id:
             dic={'sr_no':val.serial_number,
                  'questions':val.questions,
                  'resign_ques_ids': ids[0]}
             self.pool.get('resign.question').create(cr,uid,dic)
             
         for val in ques_obj.company_property_id:
             dic1={'sr_no':val.serial_number,
                  'questions':val.question,
                  'resign_com_asset_ids': ids[0]}
             self.pool.get('resign.company.asset').create(cr,uid,dic1)
             
         for val in ques_obj.company_restriction_ids:
             dic2={'sr_no':val.serial_number,
                  'item':val.item,
                  'resign_com_restriction_ids': ids[0]}
             self.pool.get('resign.company.restriction').create(cr,uid,dic2)
        
         for val in ques_obj.final_exit_interview_ques_id:
             
             dic3={'sr_no':val.serial_number,
                  'questions':val.question,
                  'final_resign_exit_ques_ids': ids[0]}
             self.pool.get('resign.final.exit.ques').create(cr,uid,dic3)
            
         self.write(cr, uid, obj.id, {'state': 'approve'})
         return True       
        
resign_information()

class hr_employee(osv.osv):
    _inherit="hr.employee"
    _columns={
        'resignation_id': fields.one2many('resign.information','employee_id','Resignation'),
        'policy_id': fields.one2many('hr.policies','emp_id','Policy'),
    }
class hr_policies(osv.osv):
    _name="hr.policies"
    _columns={
        'emp_id':fields.many2one('hr.employee','Employee'),
        'policies_id': fields.many2one('policy','Policy'),
        'start_date':fields.date('Start Policies'),
        'end_date':fields.date('End Policies'),
    }
class policy(osv.osv):
    _name="policy"
    _columns={
        'name': fields.char('Policies',size=64),
    }
    
    
class exit_interview_ques(osv.osv):
    _name = "exit.interview.ques"
    _description = "Exit Interview Question Form"
    _columns = {
        'question_ids': fields.one2many('question','question_id','Questions'),
        'company_property_ids':fields.one2many('company.property','company_property_id','Company'),    
        'sr_no_property':fields.char('Sr.No'),
        'questions_property':fields.char('Questions'),
        'answers_property':fields.char('Answer'),
    }
    
class resign_question(osv.osv):
    _name="resign.question"
    _columns={
        'resign_ques_ids':fields.many2one('resign.information','resign_ques_ids'),
        'sr_no':fields.char('Sr.No'),
        'questions':fields.char('Questions'),
        'answers':fields.char('Answer'),
    }

class resign_company_asset(osv.osv):
    _name="resign.company.asset"
    _columns={
        'resign_com_asset_ids':fields.many2one('resign.information','resign_com_asset_id'),
        'sr_no':fields.char('Sr.No'),
        'questions':fields.char('Item'),
        'tick':fields.boolean('Tick'),
        'comment':fields.char('Comment'),
    }
    
class resign_company_restriction(osv.osv):
    _name="resign.company.restriction"
    _columns={
        'resign_com_restriction_ids':fields.many2one('resign.information','resign_com_restriction_ids'),
        'sr_no':fields.char('Sr.No'),
        'item':fields.char('Item'),
        'tick':fields.boolean('Tick'),
        'comment':fields.char('Comment'),
    }

class resign_final_exit_ques(osv.osv):
    _name="resign.final.exit.ques"
    _columns={
        'final_resign_exit_ques_ids':fields.many2one('resign.information','final_resign_exit_ques_ids'),
        'sr_no':fields.char('Sr.No'),
        'questions':fields.char('Questions'),
        'answers':fields.char('Answer'),
        'interviewer_comment':fields.text('Comment'),
    }

