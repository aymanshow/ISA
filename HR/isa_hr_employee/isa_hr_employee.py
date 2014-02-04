from osv import osv
from osv import fields
import datetime
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext
class hr_employee(osv.osv):
    _name='hr.employee'
    _inherit='hr.employee'
    _columns={
            'work_experiane_line1':fields.one2many('work.experiance1','work_exp_id1','Work Experience'),
            'education_line1':fields.one2many('education.inform1','education_id1','Education Information'),
            'professional_line1':fields.one2many('professional.qualification1','professional_id1','Professional Qualification'),
            'honor_awards_line1':fields.one2many('honour.award1','honour_id1','Honours/Awards'),
            'language_spoken_line1':fields.one2many('language.spoken1','language_id1','Language Spoken'),
            
            'offer_acceptance_line1':fields.one2many('offer.acceptance1','hr_appli_id','Offer Acceptance'),
            'criminal_record_line1':fields.one2many('criminal.record1','crim_id','Criminal Record'),
            'other_certificate_line1':fields.one2many('other.certificate1','cerificate_id','Other Certificate'),
            'family_information_line1':fields.one2many('family.information1','birh_cer_id','Children Birth Information'),
            'reference_Check_line1':fields.one2many('reference.check1','hr_applicant_id','References'),
            'medical_certificate':fields.binary('Medical Certificate'),
              'residence_prove':fields.binary('Residence Approve'),
              'id_copy':fields.binary('ID Copy'),
              'passport_copy':fields.binary('Passport Copy'),
              'drives_licenses':fields.binary('Drives Licenses'),
              'working_visa':fields.binary('Working Visa'), 
               'id_gaurdian':fields.binary('ID Guardian'), 
                'health_insurance_card':fields.binary('Health Insurance Card'), 
               
                }
    


class honour_award1(osv.osv):
    _name='honour.award1' 
    _columns={
              'name':fields.char('Description',size=64),
              'local':fields.char('Local',size=64),
              'date':fields.date('Date'),
              'honour_id1':fields.many2one('hr.employee','Honour/Award'),
               }            
    
class work_experiance1(osv.osv):
    _name='work.experiance1'
    _columns={
              'name':fields.char('Company Name',size=64),
              'cargo_exercised1':fields.char('Roles & Responsibilities',size=64),
              'responsibility1':fields.char('Post & Designation',size=64),
              'start_date1':fields.date('From Date'),
              'finish_date1':fields.date('To Date'),
              'work_exp_id1':fields.many2one('hr.employee','Work Id'),
              }
class education_inform1(osv.osv):
    _name='education.inform1'
    _columns={
              'name':fields.char('Institute Attended',size=64),
              'qualification_obtain1':fields.char('Qualification Obtained',size=64),
              'start_date1':fields.date('Start Date'),
              'finish_date1':fields.date('Finish Date'),
              'education_id1':fields.many2one('hr.employee','Educational Id'),
              }
class professional_qualification1(osv.osv):
    _name='professional.qualification1'
    _columns={
               'name':fields.char('Description',size=256),
               'institute':fields.char('Institution',size=64),
               'start_date':fields.date('Start Date'),
              'finish_date':fields.date('Finish Date'),
              'professional_id1':fields.many2one('hr.employee','Professional Id'),
               }
class language_spoken1(osv.osv):
    _name='language.spoken1' 
    _columns={
              'name':fields.char('Language',size=64),
              'basic':fields.boolean('Basic'),
              'intermediate':fields.boolean('Intermediate'),
              'advance':fields.boolean('Advance'),
              'language_id1':fields.many2one('hr.employee','Language Id')
              }   
class other_certificate1(osv.osv):
    _name='other.certificate1'
    _columns={
              'name':fields.binary('Other Certificate'),
              'desc':fields.char('Certification Description',size=256),
              'cerificate_id':fields.many2one('hr.employee','Certificate Id',ondelete="cascade"),
              }
class family_information1(osv.osv):
    _name='family.information1'
    _columns={
              'child_name':fields.char('Child Name',size=64),
              'child_birth_cert':fields.binary('Birth certificate (Children)'),
              'birh_cer_id':fields.many2one('hr.employee','Birth certificate',ondelete="cascade"),
              
              }
class criminal_record1(osv.osv):
    _name="criminal.record1"
    _columns={
              'description':fields.char('Criminal Record Description',size=256),
              'crime_attachment':fields.binary('Criminal Record Attachment'),
              'crim_id':fields.many2one('hr.employee','Criminal Id'),
              }
class reference_check1(osv.osv):
    _name='reference.check1'
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
               'serial_number':fields.function(get_serial_no,type='integer',method=True,string='Sr.No',readonly=True),              'type':fields.selection([('1','Personal'),('2','Corporate')],'Type', required=True),
              'name':fields.char('Name',size=64),
              'phone_num':fields.char('Phone Number',size=64),
              'email':fields.char('Email-Id',size=64),
              'company':fields.char('Company',size=64),
              'check_mode':fields.selection([('T','Telephonic'),('P','Personal'),('E','Email')],'Check Mode'),
              'feedback':fields.text('Feed Back'),
              'hr_applicant_id':fields.many2one('hr.employee','Reference'),
               } 
class offer_acceptance1(osv.osv):
    _name='offer.acceptance1'
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'seq_num':fields.function(get_serial_no,type='integer',method=True,string='Sr.No',readonly=True),
              'prob_joing_date':fields.date('Joining Date',required=True),
              'offer_latter_acceptance_date':fields.date('Offer Letter Acceptance Date'),
              'joining_status':fields.selection([('approve','Accepted'),('pending','Pending'),('reject','Declined')],'Joining Status'),
              'attach_offer_latter':fields.binary('Attachment Offer Letter'),
              'hr_appli_id':fields.many2one('hr.employee','Offer Letter Acceptance')
              }        