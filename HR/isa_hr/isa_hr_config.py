from osv import osv
from osv import fields
import time
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext
class recruitment_form(osv.osv):
    _name='recruitment.form'
    _columns={
              'name':fields.char('Name',size=64),
               'department_id':fields.many2one('hr.department','Department',ondelete="cascade"),
              'recruitment_test_ids':fields.one2many('recruitment.test','recruitment_id','Recruitment Details'),
             'interview_ids':fields.one2many('interview.state','intr_state_id','Interview'),    
             'medical_test_ids':fields.one2many('medical.phase','medical_id','Medical Test'),  
              }
class recruitment_test(osv.osv):
    _name='recruitment.test'
    _desc='recruitment.test'
    _columns={
              'exam_name':fields.many2one('survey','Exam Name'),
              'description':fields.char('Type',size=256),
              'total_marks':fields.integer('Total Marks'),
              'min_score':fields.integer('Minimum Marks'),
              'recruitment_id':fields.many2one('recruitment.form','Recruitment Form',ondelete="cascade"),
              }
    def create(self, cr, uid, vals, context={}):
        max_marks=vals['total_marks']
        min_marks=vals['min_score']
        if max_marks >= min_marks:
            pass
        else:
            raise osv.except_osv(('Warning !'),('Minimum Marks is not greater then the total marks')) 
        return super(recruitment_test, self).create(cr, uid, vals, context)
    def onchange_exam_name(self, cr, uid, ids, exam_name, context=None):
            res={}
            survey_obj = self.pool.get('survey')
            line=survey_obj.browse(cr,uid,exam_name)
            res={
                  'description':line.type.name,
                  'total_marks':line.total_marks,
                 }
            return {'value': res}

class interview_state(osv.osv):
    _name="interview.state"
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
               'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
               'question':fields.text('Question'),
               'intr_state_id':fields.many2one('recruitment.form','recruitment form',ondelete="cascade"),
             }
class medical_phase(osv.osv):
    _name="medical.phase"
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
              'test_type':fields.char('Type Of Test',size=64),
              'medical_id':fields.many2one('recruitment.form','Medical Ids',ondelete="cascade"),
            }

    