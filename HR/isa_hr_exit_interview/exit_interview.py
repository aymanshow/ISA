from osv import fields, osv
import datetime
from datetime import datetime, timedelta
import time
from tools.translate import _
import openerp.addons.decimal_precision as dp


class exit_interview_ques(osv.osv):
    _name = "exit.interview.ques"
    _description = "Exit Interview Question Form"
    _columns = {
        'question_id': fields.one2many('question','question_ids','Questions'),
        'company_property_id':fields.one2many('company.property','company_property_ids','Company'),    
        'company_restriction_ids':fields.one2many('company.restric','company_restric_id','Company'), 
        'final_exit_interview_ques_id':fields.one2many('final.exit.interview.ques','exit_interview_ids','Company'), 
    }
    
class question(osv.osv):
    _name="question"
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
              'questions':fields.char('Questions'),
              'question_ids':fields.many2one('exit.interview.ques','Questions',ondelete="cascade"),
            }

class company_property(osv.osv):
    _name="company.property"
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
               'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
               'question':fields.char('Item'),
               'company_property_ids':fields.many2one('exit.interview.ques','Company Property',ondelete="cascade"),
             }
class company_restric(osv.osv):
    _name="company.restric"
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
               'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
               'company_restric_id':fields.many2one('exit.interview.ques','Company Restriction',ondelete="cascade"),
               'item':fields.char('Item'),
             }
    
class final_exit_interview_ques(osv.osv):
    _name="final.exit.interview.ques"
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    
    _columns={
               'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
               'exit_interview_ids':fields.many2one('exit.interview.ques','Company Restriction',ondelete="cascade"),
               'question':fields.char('Question'),
             }

#








