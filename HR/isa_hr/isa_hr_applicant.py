from osv import osv
from osv import fields
from random import choice
import string
import time
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext
AVAILABLE_STATES = [
    ('draft', 'New'),
    ('test', 'Test'),
    ('interview', 'Interview'),
    ('reference_check', 'Reference Check'),
    ('document_submission', 'Document Submission'),
    ('director_approved', 'Director_Approved'),
    ('offer_acceptance', 'Offer Acceptance'),
    ('medical_test', 'Medical Test'),
    ('joining_process', 'Joining Process'),
    ('done','Hired'),
    ('cancel', 'Rejected'),
]
AVAILABLE_STATES1 = [
    ('draft', 'New'),
    ('test', 'Test'),
    ('interview', 'Interview'),
    ('reference_check', 'Reference Check'),
    ('document_submission', 'Document Submission')]
AVAILABLE_PRIORITIES = [
    ('', ''),
    ('5', 'Not Good'),
    ('4', 'On Average'),
    ('3', 'Good'),
    ('2', 'Very Good'),
    ('1', 'Excellent')
]
#editing the stages and add some stages 
class hr_recruitment_stage(osv.osv):
        _name='hr.recruitment.stage'
        _inherit='hr.recruitment.stage'
        _columns={
                  'state': fields.selection(AVAILABLE_STATES, 'Status', required=True, help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
                  }
        _defaults = {
             'state': 'draft',
                     }
# adding the field in unique id in hr.applicant and giving the action on button shortlist this candidate it changes the state and generate the unique id     
class hr_applicant(osv.osv):
    _name='hr.applicant'
    _inherit='hr.applicant'
    _columns={
            'identification':fields.char('Employee Id'),
            'offer_acceptance_line':fields.one2many('offer.acceptance','hr_appli_id','offer_acceptance_line'),
            'joing_process_line':fields.one2many('joining.process','joining_process_id','Joining Process'),
            'doctor_name':fields.many2one('res.partner','Doctor Name'),
            'medical_test_line':fields.one2many('medical.test','medical_test_id','Medical Test'),
            'director_approved_line':fields.one2many('director.approved','director_approved_id','Director Approved'),
            'over_all_comment':fields.text('Director Comments'),
            'medical_certificate':fields.binary('Medical Certificate'),
            'photographs':fields.binary('Photograph'),
            'residence_prove':fields.binary('Residence prove'),
            'id_copy':fields.binary('I.D copy'),
            'bank_account_no':fields.char('Bank account No',size=64),
            'social_security_no':fields.char('Social Security Number',size=64),
            'passport_copy':fields.binary('Passport copy'),
            'drives_licenses':fields.binary('Drives Licenses'),
            'survey_ids':fields.one2many('survey.test.line','aplicant_id','Technical Test'),
            'working_visa':fields.binary('Working Visa'),
            'id_gaurdian':fields.binary('I.D of Guardian'),
            'health_insurance_card':fields.binary('Health insurance card'),
            'declarations':fields.binary('Declarations'),
            'no_children':fields.integer('Number Of Children'),
            'criminal_record_line':fields.one2many('criminal.record','crim_id','Criminal Record'),
            'other_certificate_line':fields.one2many('other.certificate','cerificate_id','Other Certificate'),
            'family_information_line':fields.one2many('family.information','birh_cer_id','Children Birth Information'),
            'reference_check_line':fields.one2many('reference.check','hr_applicant_id','Reference Check'),
            'work_experiane_line':fields.one2many('work.experiance','work_exp_id','Work Experience'),
            'education_line':fields.one2many('education.inform','education_id','Education Information'),
            'professional_line':fields.one2many('professional.qualification','professional_id1','Professional Qualification'),
            'honor_awards_line':fields.one2many('honour.award','honour_id','Honours/Awards'),
            'language_spoken_line':fields.one2many('language.spoken','language_id','Language Spoken'),
            'over_all_rating': fields.selection(AVAILABLE_PRIORITIES, 'Over All Rating'),
            'attachment':fields.binary('Attachment'),
            'comment':fields.text('Comment'),
            'department_id':fields.many2one('hr.department','Department'),
            'hr_applicant_id':fields.many2one('hr.applicant','Hr applicant Id'),
            'candidate_id':fields.char('Applicant Id',size=64,help='First generate the unique id the process further',readonly=True),
            'requestion_id':fields.many2one('drishti.hr','Requisition Id',domain=[('state', '=', 'confirmed')],help='Enter the Unique Id which is approved.',ondelete="cascade"),
            'inter_line':fields.one2many('interview.sta','dumy_id1','Interview Form'),
#       Test State form design field required       
              'test_line':fields.one2many('test.stage.form','recruitment_id','Test Stage Form'),
              'applicant_name':fields.char('Applicant Name',size=64),
              'description':fields.text('Description'),
              'employee_id':fields.many2one('hr.employee','Employee Id',help='Person Name whose taking the Test'),
              'state': fields.related('stage_id', 'state', type="selection", store=True,
                selection=AVAILABLE_STATES, string="Status", readonly=True,
                help='The status is set to \'Draft\', when a case is created.\
                      If the case is in progress the status is set to \'Open\'.\
                      When the case is over, the status is set to \'Done\'.\
                      If the case needs to be reviewed then the status is \
                      set to \'Pending\'.'),
              'user_id':fields.many2one('res.users','User Id'),
              'password':fields.char('Password'),
              'is_interview_scheduled':fields.boolean('Interview Scheduled'),
              }
    _default={
               'is_interview_scheduled':False
              }
               
    
#function for mail configuration in the state of director approved 
    
    def action_offer_acceptance_mail(self, cr, uid, ids, context=None):
            dic=[]
            obj=self.browse(cr,uid,ids[0])
            partner_obj=self.pool.get('res.partner')
            for res in obj.joing_process_line:
                if res.joing_attachment==True:
                    search_id=partner_obj.search(cr,uid,[('email','=',res.email_id)])
                    if search_id:
                        dic.append(search_id[0])
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            ir_model_fields=self.pool.get('ir.model.fields')
            ir_model_fields_ids_offer_acceptance=ir_model_fields.search(cr,uid,[('name','ilike','applicant_name')])
            if ir_model_fields_ids_offer_acceptance:
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.applicant'),('model_object_field','=',ir_model_fields_ids_offer_acceptance[0])], context=context)
                if template_ids:
                        values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                        email_obj=self.browse(cr,uid,ids[0])
                        try:
                            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                        except ValueError:
                            compose_form_id = False 
                        values['email_to'] = dic
                        values['res_id'] = False
                        mail_mail_obj = self.pool.get('mail.mail')
                        msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                        if msg_id:
                            mail_mail_obj.send(cr, uid, [msg_id], context=context)
                        ctx = dict(context)
                        ctx['default_partner_ids'] = dic
                        ctx['default_template_id'] = template_ids[0]
                        return {
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'mail.compose.message',
                                'views': [(compose_form_id, 'form')],
                                'view_id': compose_form_id,
                                'target': 'new',
                                'context': ctx,
                            }
    def action_medical_inform_send(self, cr, uid, ids, context=None):
            test=[]
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            ir_model_fields=self.pool.get('ir.model.fields')
            ir_model_fields_ids_medical=ir_model_fields.search(cr,uid,[('name','=','doctor_name')])
            if ir_model_fields_ids_medical[0]:
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.applicant'),('model_object_field','=',ir_model_fields_ids_medical[0])], context=context)
                if template_ids:
                        values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                        email_obj=self.browse(cr,uid,ids[0])
                        try:
                            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                        except ValueError:
                            compose_form_id = False 
                        
                        if not email_obj.email_from:
                            raise osv.except_osv(
                                        _('Error!'),
                                        _('Please fill the applicant email address'))
                        else:
                             test.append(email_obj.email_from)
                        if not email_obj.doctor_name.email:
                            raise osv.except_osv(
                                        _('Error!'),
                                        _('Please fill the doctor Email Address '))
                        else:
                            test.append(email_obj.doctor_name.email)
                        values['email_to'] = test
                        values['res_id'] = False
                        mail_mail_obj = self.pool.get('mail.mail')
                        msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                        if msg_id:
                            mail_mail_obj.send(cr, uid, [msg_id], context=context)
                        ctx = dict(context)
                        ctx['default_template_id'] = template_ids[0]
                        return {
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'mail.compose.message',
                                'views': [(compose_form_id, 'form')],
                                'view_id': compose_form_id,
                                'target': 'new',
                                'context': ctx,
                            }
    def action_send_test_email(self, cr, uid, ids, context=None):
            dic=[]
            obj=self.browse(cr,uid,ids[0])
            partner_obj=self.pool.get('res.partner')
            for res in obj.joing_process_line:
                if res.joing_attachment==True:
                    search_id=partner_obj.search(cr,uid,[('email','=',res.email_id)])
                    if search_id:
                        dic.append(search_id[0])
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            ir_model_fields=self.pool.get('ir.model.fields')
            ir_model_fields_ids_test=ir_model_fields.search(cr,uid,[('name','=','survey')])
            if ir_model_fields_ids_test:
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.applicant'),('model_object_field','=',ir_model_fields_ids_test[0])], context=context)
                if template_ids:
                        values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                        email_obj=self.browse(cr,uid,ids[0])
                        try:
                            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                        except ValueError:
                            compose_form_id = False 
                        values['email_to'] = dic
                        values['res_id'] = False
                        mail_mail_obj = self.pool.get('mail.mail')
                        msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                        if msg_id:
                            mail_mail_obj.send(cr, uid, [msg_id], context=context)
                        ctx = dict(context)
                        ctx['default_partner_ids'] = dic
                        ctx['default_template_id'] = template_ids[0]
                        return {
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'mail.compose.message',
                                'views': [(compose_form_id, 'form')],
                                'view_id': compose_form_id,
                                'target': 'new',
                                'context': ctx,
                            }
   # mail for interview stage 
    def action_send_joining_process_email(self, cr, uid, ids, context=None):
            dic=[]
            obj=self.browse(cr,uid,ids[0])
            partner_obj=self.pool.get('res.partner')
            for res in obj.joing_process_line:
                if res.joing_attachment==True:
                    search_id=partner_obj.search(cr,uid,[('email','=',res.email_id)])
                    if search_id:
                        dic.append(search_id[0])
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            ir_model_fields=self.pool.get('ir.model.fields')
            ir_model_fields_ids_joining=ir_model_fields.search(cr,uid,[('name','ilike','identification')])
            if ir_model_fields_ids_joining:
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.applicant'),('model_object_field','=',ir_model_fields_ids_joining[0])], context=context)
                if template_ids:
                        values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                        email_obj=self.browse(cr,uid,ids[0])
                        try:
                            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                        except ValueError:
                            compose_form_id = False 
                        values['email_to'] = dic
                        values['res_id'] = False
                        mail_mail_obj = self.pool.get('mail.mail')
                        msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                        if msg_id:
                            mail_mail_obj.send(cr, uid, [msg_id], context=context)
                        ctx = dict(context)
                        ctx['default_partner_ids'] = dic
                        ctx['default_template_id'] = template_ids[0]
                        return {
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'mail.compose.message',
                                'views': [(compose_form_id, 'form')],
                                'view_id': compose_form_id,
                                'target': 'new',
                                'context': ctx,
                                 }    
                        
                        
    def action_interview_send(self, cr, uid, ids, context=None):
            test=[]
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.applicant')], context=context)
            if template_ids:
                    values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                    email_obj=self.browse(cr,uid,ids[0])
                    try:
                        compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                    except ValueError:
                        compose_form_id = False 
                    
                    if not email_obj.email_from:
                        raise osv.except_osv(
                                    _('Error!'),
                                    _('Please fill the applicant email address'))
                    else:
                         test.append(email_obj.email_from)
                    values['email_to'] = test
                    values['res_id'] = False
                    mail_mail_obj = self.pool.get('mail.mail')
                    msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                    if msg_id:
                        mail_mail_obj.send(cr, uid, [msg_id], context=context)
                    ctx = dict(context)
                    ctx['default_template_id'] = template_ids[3]
                    return {
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'mail.compose.message',
                            'views': [(compose_form_id, 'form')],
                            'view_id': compose_form_id,
                            'target': 'new',
                            'context': ctx,
                        }

    
#for previous move to the next stage medical test
    def action_accepted(self, cr, uid, ids, context=None):
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id8=value1.search(cr ,uid ,[('state','=','medical_test')],context=context)
        obj=self.browse(cr,uid,ids[0])
        if obj.state=='offer_acceptance':
            if not obj.offer_acceptance_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Offer acceptance Information'))
            else:
                    record8= value1.browse(cr,uid,record_id8[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record8.id})
        return True
    def action_pass(self, cr, uid, ids, context=None):
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id8=value1.search(cr ,uid ,[('state','=','reference_check')],context=context)
        record_id7=value1.search(cr ,uid ,[('state','=','offer_acceptance')],context=context)
        obj=self.browse(cr,uid,ids[0])
        if obj.state=='interview':
            if not obj.inter_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Interview Information'))
            else:
                    record8= value1.browse(cr,uid,record_id8[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record8.id})
        if obj.state=='director_approved':
                    record7= value1.browse(cr,uid,record_id7[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record7.id})
        return True
    def action_submit(self, cr, uid, ids, context=None):
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id8=value1.search(cr ,uid ,[('state','=','director_approved')],context=context)
        obj=self.browse(cr,uid,ids[0])
        if obj.state=='document_submission':
                    record8= value1.browse(cr,uid,record_id8[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record8.id})
        return True
#for previous move to the next stage joining process
    def action_cleared(self, cr, uid, ids, context=None):
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id9=value1.search(cr ,uid ,[('state','=','joining_process')],context=context)
        obj=self.browse(cr,uid,ids[0])
        if obj.state=='medical_test':
            if not obj.medical_test_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Medical Test Information'))
            else:            
                    record9= value1.browse(cr,uid,record_id9[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record9.id})
        return True
    def action_done(self, cr, uid, ids, context=None):
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id9=value1.search(cr ,uid ,[('state','=','document_submission')],context=context)
        obj=self.browse(cr,uid,ids[0])
        if obj.state=='reference_check':
            if not obj.reference_check_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Reference Check Information'))
            else:
                    record9= value1.browse(cr,uid,record_id9[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record9.id})
        return True
 # hire and create the employee and fill the information in the employee form
    def case_close_with_emp(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        hr_employee = self.pool.get('hr.employee')
        value1 = self.pool.get('hr.recruitment.stage')
        obj=self.browse(cr,uid,ids[0])
        hr_job_contract=self.pool.get('hr.contract')
        hr_job_obj=self.pool.get('hr.job')
        hr_requestion_obj=self.pool.get('drishti.hr')
        record_id10=value1.search(cr ,uid ,[('state','=','done')],context=context)
        if obj.state=='joining_process':
                    record10= value1.browse(cr,uid,record_id10[0],context=context)
                    hr_applicant_obj=self.browse(cr,uid,obj.id)
                    job_id=self.pool.get('hr.job').search(cr,uid,[('state','=','recruit'),('department_id','=',obj.department_id.id)])
                    if not job_id:
                          raise osv.except_osv(_('Warning!'), _('You must define the job position .'))     
                    else:
                        job_obj=self.pool.get('hr.job').browse(cr,uid,job_id[0])
                        self.write(cr, uid, ids,{'stage_id':record10.id})
        model_data = self.pool.get('ir.model.data')
        act_window = self.pool.get('ir.actions.act_window')
        emp_id = False
        for applicant in self.browse(cr, uid, ids, context=context):
            address_id = False
            if applicant.partner_id:
                address_id = self.pool.get('res.partner').address_get(cr,uid,[applicant.partner_id.id],['contact'])['contact']
            if applicant.job_id:
                    applicant.job_id.write({'no_of_recruitment': applicant.job_id.no_of_recruitment - 1})
                    dict={'name': applicant.partner_name or applicant.name,
                          'job_id': applicant.job_id.id,
                          'address_home_id': address_id,
                          'department_id': applicant.department_id.id,
                         }
                    
                    emp_id = self.pool.get('hr.employee').create(cr,uid,dict)
                    if applicant.job_id.no_of_recruitment==0.0:
                        hr_job_obj.job_open(cr, uid, applicant.job_id.id)
                        requestion_id1=hr_requestion_obj.search(cr,uid,[('id','=',obj.requestion_id.id)])
                        hr_requestion_obj.write(cr,uid,requestion_id1,{'state':'done'})
                         
                    for val in applicant.offer_acceptance_line:
                        if not val.prob_joing_date:
                            raise osv.except_osv(_('Warning!'), _('You must define the joining date in the recruitment process .'))
                        else:
                            if val.joining_status=='approve':
                                    date_joing=val.prob_joing_date
                                    date_from_year = int(val.prob_joing_date[:4])
                                    date_from_month = int(val.prob_joing_date[5:7])
                                    date_from_date = int(val.prob_joing_date[8:10])
                                    from datetime import date
                                    from dateutil.relativedelta import relativedelta
                                    date_after_3months = date(date_from_year,date_from_month,date_from_date) + relativedelta(months = +3)
                                    hr_employee.write(cr, uid,emp_id, {'renewal_date': date_after_3months},context=context)
                                    vals=hr_job_contract.create(cr,uid,{'name':applicant.name,
                                                                   'employee_id':emp_id,
                                                                   'wage':0.00,
                                                                   'date_start':val.prob_joing_date,
                                                                   'date_end':date_after_3months,
                                                                         })
                    self.write(cr, uid, applicant.id, {'emp_id': emp_id}, context=context)
                    if emp_id:
                        emp_obj=hr_employee.browse(cr,uid,emp_id)
                        self.write(cr, uid, applicant.id, {'identification': emp_obj.identification_id}, context=context)
                    self.case_close(cr, uid, [applicant.id], context)
            else:
                raise osv.except_osv(_('Warning!'), _('You must define Applied Job for this applicant.'))
            
            if not obj.work_experiane_line:
               raise osv.except_osv(_('Warning!'), _('You can not fill working Experiance for this applicant')) 
            for res in obj.work_experiane_line:
                lst=[]
                lst.append((0,0,{'name':res.name,'cargo_exercised1':res.cargo_exercised,'responsibility1':res.responsibility,'start_date1':res.start_date,'finish_date1':res.finish_date})),
                hr_employee.write(cr,uid,emp_id,{'work_experiane_line1':lst})
            if not obj.education_line:
               raise osv.except_osv(_('Warning!'), _('You can not fill Candidate education information')) 
            for res in obj.education_line:
                lst=[]
                lst.append((0,0,{'name':res.name,'qualification_obtain1':res.qualification_obtain,'start_date1':res.start_date,'finish_date1':res.finish_date})),
                hr_employee.write(cr,uid,emp_id,{'education_line1':lst})
            if not obj.professional_line:
               raise osv.except_osv(_('Warning!'), _('You can not fill Candidate professional information')) 
            for res in obj.professional_line:
                lst=[]
                lst.append((0,0,{'name':res.name,'institute':res.institute,'start_date':res.start_date,'finish_date':res.finish_date})),
                hr_employee.write(cr,uid,emp_id,{'professional_line1':lst})
            if not obj.honor_awards_line:
               raise osv.except_osv(_('Warning!'), _('You can not fill Candidate honor award')) 
            for res in obj.honor_awards_line:
                lst=[]
                lst.append((0,0,{'name':res.name,'local':res.local,'date':res.date})),
                hr_employee.write(cr,uid,emp_id,{'honor_awards_line1':lst})
            if not obj.language_spoken_line:
               raise osv.except_osv(_('Warning!'), _('You can not fill language spoken information')) 
            for res in obj.language_spoken_line:
                lst=[]
                lst.append((0,0,{'name':res.name,'basic':res.basic,'intermediate':res.intermediate,'advance':res.advance})),
                hr_employee.write(cr,uid,emp_id,{'language_spoken_line1':lst})
            if not obj.offer_acceptance_line:
               raise osv.except_osv(_('Warning!'), _('You can not fill offer acceptance information')) 
            for res in obj.offer_acceptance_line:
                lst=[]
                lst.append((0,0,{'seq_num':res.seq_num,'prob_joing_date':res.prob_joing_date,'offer_latter_acceptance_date':res.offer_latter_acceptance_date,'joining_status':res.joining_status,'attach_offer_latter':res.attach_offer_latter})),
                hr_employee.write(cr,uid,emp_id,{'offer_acceptance_line1':lst})
                hr_employee.write(cr,uid,emp_id,{'joining_date':res.prob_joing_date})
            if not obj.offer_acceptance_line:
               pass
            else: 
                for res in obj.criminal_record_line:
                    lst=[]
                    lst.append((0,0,{'description':res.description,'crime_attachment':res.crime_attachment})),
                    hr_employee.write(cr,uid,emp_id,{'criminal_record_line1':lst})
            if not obj.family_information_line:
               pass
            else:
                for res in obj.family_information_line:
                    lst=[]
                    lst.append((0,0,{'child_name':res.child_name,'child_birth_cert':res.child_birth_cert})),
                    hr_employee.write(cr,uid,emp_id,{'family_information_line1':lst})
            if not obj.reference_check_line:
                pass
            else:
                for res in obj.reference_check_line:
                    lst=[]
                    lst.append((0,0,{'serial_number':res.serial_number,'type':res.type,'name':res.name,'phone_num':res.phone_num,'email':res.email,'company':res.company,'check_mode':res.check_mode,'feedback':res.feedback})),
                    hr_employee.write(cr,uid,emp_id,{'reference_Check_line1':lst})
            if not obj.medical_certificate:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'medical_certificate':obj.medical_certificate})
            if not obj.residence_prove:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'residence_prove':obj.residence_prove})
            if not obj.id_copy:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'id_copy':obj.id_copy})
            if not obj.passport_copy:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'passport_copy':obj.passport_copy})
            if not obj.drives_licenses:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'drives_licenses':obj.drives_licenses})
            if not obj.working_visa:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'working_visa':obj.working_visa})
            if not obj.id_gaurdian:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'id_gaurdian':obj.id_gaurdian})
            if not obj.photographs:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'image_medium':obj.photographs})
            if not obj.health_insurance_card:
                pass
            else:
                hr_employee.write(cr,uid,emp_id,{'health_insurance_card':obj.health_insurance_card})
        action_model, action_id = model_data.get_object_reference(cr, uid, 'hr', 'open_view_employee_list')
        dict_act_window = act_window.read(cr, uid, action_id, [])
        if emp_id:
            dict_act_window['res_id'] = emp_id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window
#this mail is regarding to the applicant inform for the test
    def action_quotation_send4(self, cr, uid, ids, context=None):
            test=[]
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.applicant')], context=context)
            if template_ids:
                    values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                    email_obj=self.browse(cr,uid,ids[0])
                    try:
                        compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                    except ValueError:
                        compose_form_id = False 
                    
                    if not email_obj.email_from:
                        raise osv.except_osv(
                                    _('Error!'),
                                    _('Please fill the applicant email address'))
                    else:
                         test.append(email_obj.email_from)
                    values['email_to'] = test
                    values['res_id'] = False
                    mail_mail_obj = self.pool.get('mail.mail')
                    msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                    if msg_id:
                        mail_mail_obj.send(cr, uid, [msg_id], context=context)
                    ctx = dict(context)
                    ctx['default_template_id'] = template_ids[3]
                    return {
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'mail.compose.message',
                            'views': [(compose_form_id, 'form')],
                            'view_id': compose_form_id,
                            'target': 'new',
                            'context': ctx,
                        }
    
#Function for Approve the stage and go to the next stage
    def action_approve(self,cr,uid,ids,context=None):
        a=0
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id1=value1.search(cr ,uid ,[('state','=','draft')],context=context)
        record_id2=value1.search(cr ,uid ,[('state','=','test')],context=context)
        record_id3=value1.search(cr ,uid ,[('state','=','interview')],context=context)
        record_id4=value1.search(cr ,uid ,[('state','=','reference_check')],context=context)
        record_id5=value1.search(cr ,uid ,[('state','=','document_submission')],context=context)
        record_id6=value1.search(cr ,uid ,[('state','=','director_approved')],context=context)
        record_id7=value1.search(cr ,uid ,[('state','=','offer_acceptance')],context=context)
        record_id8=value1.search(cr ,uid ,[('state','=','medical_test')],context=context)
        record_id9=value1.search(cr ,uid ,[('state','=','joining_process')],context=context)
        record_id10=value1.search(cr ,uid ,[('state','=','done')],context=context)
        record_id11=value1.search(cr ,uid ,[('state','=','cancel')],context=context)
        obj=self.browse(cr,uid,ids[0])
        if obj.state=='cancel':
                    record11= value1.browse(cr,uid,record_id11[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record11.id})
        if obj.state=='draft':
                    record2= value1.browse(cr,uid,record_id2[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record2.id})
        if obj.state=='test':
                    record3= value1.browse(cr,uid,record_id3[0],context=context)
                    for val in obj.survey_ids:
                        if val.marks >= val.min_score1:
                            continue
                            if val.marks <= val.total_marks1:
                                     continue
                            else:
                               raise osv.except_osv(_('Attention!'),_('Candidate Can not scored more then total marks!'))      
                        else:
                            a=1
                    if a == 1:
                        record11= value1.browse(cr,uid,record_id11[0],context=context)
                        self.write(cr, uid, ids,{'stage_id':record11.id})
                        raise osv.except_osv(_('Attention!'),_('Candidate has not scored minimum marks for qualifying for next level of interview process !'))
                    else:
                        self.write(cr, uid, ids,{'stage_id':record3.id})
        if obj.state=='interview':
            if not obj.inter_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Interview Information '))
            else:
                    record4= value1.browse(cr,uid,record_id4[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record4.id})
        if obj.state=='reference_check':
            if not obj.reference_check_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Reference Check Information'))
            else:
                    record5= value1.browse(cr,uid,record_id5[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record5.id})
        if obj.state=='document_submission':
                    record6= value1.browse(cr,uid,record_id6[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record6.id})
        if obj.state=='director_approved':
                    record7= value1.browse(cr,uid,record_id7[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record7.id})
        if obj.state=='offer_acceptance':
            if not obj.offer_acceptance_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Offer acceptance Information'))
            else:
                    record8= value1.browse(cr,uid,record_id8[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record8.id})
        if obj.state=='medical_test':
            if not obj.medical_test_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Medical Test Information'))
            else:            
                    record9= value1.browse(cr,uid,record_id9[0],context=context)
                    self.write(cr, uid, ids,{'stage_id':record9.id})
        if obj.state=='joining_process':
            if not obj.joing_process_line:
                    raise osv.except_osv(('Warning !'),('Please fill the Joining Information '))
            else:
                    record10= value1.browse(cr,uid,record_id10[0],context=context)
                    hr_applicant_obj=self.browse(cr,uid,obj.id)
                    job_id=self.pool.get('hr.job').search(cr,uid,[('state','=','recruit'),('unique_id1','=',hr_applicant_obj.requestion_id.id)])
                    job_obj=self.pool.get('hr.job').browse(cr,uid,job_id[0])
                    self.write(cr, uid, ids,{'stage_id':record10.id})
        return True


#Function if any state Fail the applicant then it is directly go to the Cancel state the 
    def case_cancel(self, cr, uid, ids, context=None):
        """Overrides cancel for crm_case for setting probability
        """
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id11=value1.search(cr ,uid ,[('state','=','cancel')],context=context)
        record1= value1.browse(cr,uid,record_id11[0],context=context)
        vals=record1.id
        self.write(cr, uid, ids, {'stage_id': vals})
        res = super(hr_applicant, self).case_cancel(cr, uid, ids, context)
        return res

# THis onchange works for requestion_id which is generated in the requestion form is used and according to the requestionid we fill the name and department id

    def onchange_requestion_id(self,cr,uid,ids,requestion_id,context=None):
             res={}
             info=''
             drishtihr_obj=self.pool.get('drishti.hr')
             drishtihr_ids=drishtihr_obj.search(cr ,uid ,[('state','=','confirmed')])
             line= drishtihr_obj.browse(cr,uid,requestion_id)
             if  requestion_id in drishtihr_ids:
                 res ={
                       'name':line.name,
                       'department_id':line.department_id.id,
                       'job_id':line.designation.id,
                       
                     } 
             return {'value': res}
    def onchange_employee_id(self,cr,uid,ids,employee_id,context=None):
             res={}
             info=''
             employee_obj=self.pool.get('hr.employee')
             obj=self.browse(cr,uid,ids)
             employee_ids=employee_obj.search(cr ,uid ,[('id','=',employee_id)])
             line= employee_obj.browse(cr,uid,employee_ids[0])
             if  employee_ids:
                 res ={
                       'department_id':line.department_id.id,
                      'email_from':line.work_email,
                        } 
             return {'value': res}
# genrate the random password for the applicant
    def genpasswd(self):
        chars = string.letters + string.digits
        return ''.join([choice(chars) for i in range(6)])
#Create the unique id for the applicant which we track the stage of the applicant and fill the details in the test, interview and and the medical test through the test configure menu
    def action_create_unique_id(self,cr,uid,ids,context=None):
        list=[]
        value = self.pool.get('ir.sequence').get(cr, uid, 'hr.applicant')
        value1 = self.pool.get('hr.recruitment.stage')
        mod_obj = self.pool.get('ir.model.data')
        record_id=value1.search(cr ,uid ,[('state','=','test')],context=context)
        obj=self.browse(cr,uid,ids[0])
        recruit_obj=self.pool.get('recruitment.form')
        recruit_id=recruit_obj.search(cr,uid,[('department_id','=',obj.department_id.id)])
    ###create the user and fill in the survey test line in the test stage
        user_obj = self.pool.get('res.users')
        if not obj.work_experiane_line:
            raise osv.except_osv(('Warning !'),('Please fill the details of work experience.'))
        else:
           for a in  obj.work_experiane_line:
                if a.start_date < a.finish_date:
                    pass
                else:
                    raise osv.except_osv(('Warning !'),('In Work Experience Tab From date mentioned is not appropriate'))
        if not obj.education_line:
            raise osv.except_osv(('Warning !'),('Please fill the details of Education.'))
        else:
            for a in  obj.education_line:
                if a.start_date < a.finish_date:
                    pass
                else:
                    raise osv.except_osv(('Warning !'),('In Education Tab From date mentioned is not appropriate'))
        if not obj.professional_line:
            raise osv.except_osv(('Warning !'),('Please fill the details of Professional line.'))
        else:
            for a in obj.professional_line:
                if a.start_date < a.finish_date:
                    pass
                else:
                    raise osv.except_osv(('Warning !'),('In Professional Tab From date mentioned is not appropriate'))
        if not obj.language_spoken_line:
            raise osv.except_osv(('Warning !'),('Please fill the details of Language Spoken.'))
        else:
            for a in obj.language_spoken_line:
                if a.basic==True and a.intermediate==True and a.advance==True:
                     raise osv.except_osv(('Warning !'),('Please select any one option in basic or intermediate or advance Level Language spoken tab '))
                if a.basic==True and a.intermediate==True:
                    raise osv.except_osv(('Warning !'),('Please select any one option in basic or Intermediate Language spoken tab'))
                if a.advance==True and a.basic==True:
                    raise osv.except_osv(('Warning !'),('Please select any one option in basic or advance Language spoken tab'))
                if a.intermediate==True and a.advance==True:
                    raise osv.except_osv(('Warning !'),('Please select any one option in intermediate or advance Language spoken tab'))
                else:
                    pass
        passwd= self.genpasswd()
        vals_user = {
               'name':obj.partner_name,
               'login':obj.email_from,
               'password':passwd,
            }
        user=user_obj.create(cr, uid, vals_user, context)
        self.write(cr,uid,ids,{'user_id':user})
        self.write(cr,uid,ids,{'user_id':user,'password':passwd})
        if not recruit_id:
            raise osv.except_osv(('Warning !'),('Please Configuration the test survey'))
        else:
            st=self.pool.get('survey.test.line').browse(cr,uid,recruit_id[0])
        if not st:
             raise osv.except_osv(('Warning !'),('Please configure the survey Test.'))
        if not recruit_id:
            raise osv.except_osv(('Warning !'),('Please configure the Department Test.'))
        else:
            stage=self.pool.get('recruitment.form').browse(cr,uid,recruit_id[0])
        if not stage.recruitment_test_ids:
             raise osv.except_osv(('Warning !'),('Please configure the test.'))
        else:
            list.append(user)
            list=[]
            for val in stage.recruitment_test_ids:
                  cr_id=self.pool.get('survey.test.line').create(cr,uid,{'survey_id':val.exam_name.id,'total_marks1':val.total_marks,'min_score1':val.min_score,'user_id':user,'aplicant_id':obj.id})
                  survey_obj=self.pool.get('survey').browse(cr,uid,val.exam_name.id)
                  self.pool.get('survey').write(cr,uid,survey_obj.id,{'invited_user_ids':[[6,0,list]]})
        if not stage.interview_ids:
            raise osv.except_osv(('Warning !'),('Please configure the Interview.'))
        else:
            list = []
            for sal in stage.interview_ids:
                list.append((0,0,{'seq_num':sal.serial_number,'quest':sal.question})),
            record= value1.browse(cr,uid,record_id[0],context=context)
            self.write(cr,uid,obj.id,{'inter_line':list})
        if not stage.medical_test_ids:
            raise osv.except_osv(('Warning !'),('Please configure the Medical test.'))
        else:
            list = []
            for rec in stage.medical_test_ids:
                    list.append((0,0,{'seq_num':rec.serial_number,'type_of_test':rec.test_type})),
            record= value1.browse(cr,uid,record_id[0],context=context)
            self.write(cr,uid,obj.id,{'medical_test_line':list})
        vals=record.id
        self.write(cr, uid, ids,{'candidate_id': value,'stage_id':vals,})
        return True
    _defaults = {
             'state': 'draft',
              }
#calender view for medical test schedule
    def action_calender(self, cr, uid, ids, context=None):
        """ This opens Meeting's calendar view to schedule meeting on current applicant
            @return: Dictionary value for created Meeting view
        """
        applicant = self.browse(cr, uid, ids[0], context)
        category = self.pool.get('ir.model.data').get_object(cr, uid, 'hr_recruitment', 'categ_meet_interview', context)
        res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid, 'base_calendar', 'action_crm_meeting', context)
        res['context'] = {
            'default_partner_ids': applicant.partner_id and [applicant.partner_id.id] or False,
            'default_user_id': uid,
            'default_name': applicant.name,
            'default_categ_ids': category and [category.id] or False,
        }
        return res
class honour_award(osv.osv):
    _name='honour.award' 
    _columns={
              'name':fields.char('Description',size=64),
              'local':fields.char('Local',size=64),
              'date':fields.date('Date'),
              'honour_id':fields.many2one('hr.applicant','Honour/Award'),
               }            
    
class work_experiance(osv.osv):
    _name='work.experiance'
    _columns={
              'name':fields.char('Company Name',size=64),
              'cargo_exercised':fields.char('Roles & Responsibilities',size=64),
              'responsibility':fields.char('Post & Designation',size=64),
              'start_date':fields.date('From Date'),
              'finish_date':fields.date('To Date'),
              'work_exp_id':fields.many2one('hr.applicant','Work Id'),
              }
class education_inform(osv.osv):
    _name='education.inform'
    _columns={
              'name':fields.char('Institute Attended',size=64),
              'qualification_obtain':fields.char('Qualification Obtained',size=64),
              'start_date':fields.date('Start Date'),
              'finish_date':fields.date('Finish Date'),
              'education_id':fields.many2one('hr.applicant','Educational Id'),
              }
class professional_qualification(osv.osv):
    _name='professional.qualification'
    _columns={
               'name':fields.char('Description',size=256),
               'institute':fields.char('Institution',size=64),
               'start_date':fields.date('Start Date'),
              'finish_date':fields.date('Finish Date'),
              'professional_id1':fields.many2one('hr.applicant','Professional Id'),
               }
class language_spoken(osv.osv):
    _name='language.spoken' 
    _columns={
              'name':fields.char('Language',size=64),
              'basic':fields.boolean('Basic'),
              'intermediate':fields.boolean('Intermediate'),
              'advance':fields.boolean('Advance'),
              'language_id':fields.many2one('hr.applicant','Language Id')
              }   
class test_stage_form(osv.osv):
    _name='test.stage.form'
    _columns={
              'exam_name1':fields.char('Exam Name',size=64,readonly=True),
              'total_marks1':fields.integer('Total Marks',readonly=True),
              'min_score1':fields.integer('Minimum Marks',readonly=True),
              'scored':fields.integer('Scored'),
              'attach':fields.binary('Attachment'),
              'comment':fields.char('Comment',size=256),
              'recruitment_id':fields.many2one('hr.applicant','Recruitment Form',ondelete="cascade"),
             }
class interview_sta(osv.osv):
    _name='interview.sta'
    _columns={
              'seq_num' : fields.char('Sr No',size=64,readonly=True),
              'quest':fields.text('Question',readonly=True),
              'rating': fields.selection(AVAILABLE_PRIORITIES, 'Rating'),
              'comment':fields.text('Comment'),
              'dumy_id1':fields.many2one('hr.applicant','Dummy','Interview '),
              }
class reference_check(osv.osv):
    _name='reference.check'
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'serial_number':fields.function(get_serial_no,type='integer',method=True,string='Sr.No',readonly=True),
              'type':fields.selection([('1','Personal'),('2','Corporate')],'Type', required=True),
              'name':fields.char('Name',size=64),
              'phone_num':fields.char('Phone Number',size=64),
              'email':fields.char('Email-Id',size=64),
              'company':fields.char('Company',size=64),
              'check_mode':fields.selection([('T','Telephonic'),('P','Personal'),('E','Email')],'Check Mode'),
              'feedback':fields.text('Feed Back'),
              'hr_applicant_id':fields.many2one('hr.applicant','Reference'),
              } 
class other_certificate(osv.osv):
    _name='other.certificate'
    _columns={
              'name':fields.binary('Other Certificate'),
              'desc':fields.char('Certification Description',size=256),
              'cerificate_id':fields.many2one('hr.applicant','Certificate Id',ondelete="cascade"),
              }
class family_information(osv.osv):
    _name='family.information'
    _columns={
              'child_name':fields.char('Child Name',size=64),
              'child_birth_cert':fields.binary('Birth certificate (Children)'),
              'birh_cer_id':fields.many2one('hr.applicant','Birth certificate',ondelete="cascade"),
              }
class criminal_record(osv.osv):
    _name="criminal.record"
    _columns={
              'description':fields.char('Criminal Record Description',size=256),
              'crime_attachment':fields.binary('Criminal Record Attachment'),
              'crim_id':fields.many2one('hr.applicant','Criminal Id'),
              }    
class director_approved(osv.osv):
    _name="director.approved"
    _columns={
              'seq_num' : fields.char('Stage',size=64),
              'comment':fields.text('Comment'),
              'state1': fields.selection(AVAILABLE_STATES1, 'Stage', help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
              'director_approved_id':fields.many2one('hr.applicant','Director Approved'),
              }
    
class medical_test(osv.osv):
    _name='medical.test' 
    _columns={
              'seq_num' : fields.char('Sr.No',size=64,readonly=True),
              'type_of_test':fields.char('Type Of Test',size=64,readonly=True),
              'result':fields.binary('Result'),
              'medical_test_id':fields.many2one('hr.applicant','Medical Test'),
              } 
class joining_process(osv.osv):
    _name='joining.process'  
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'seq_num':fields.function(get_serial_no,type='integer',method=True,string='Sr.No',readonly=True),        
              'name':fields.many2one('hr.employee','Employee Name',required=True),
              'email_id':fields.char('Email Id',size=64,required=True),
              'joing_attachment':fields.boolean('Send Mail'),
              'joining_process_id':fields.many2one('hr.applicant','Joining Process'),
              }
    def onchange_name(self,cr,uid,ids,name,context=None):
             res={}
             emp_obj=self.pool.get('hr.employee')
             emp_ids=emp_obj.search(cr,uid,[('name','=','name')])
             line=emp_obj.browse(cr,uid,name)
             res={
                 'email_id':line.work_email
                 }
             return {'value': res}
class offer_acceptance(osv.osv):
    _name='offer.acceptance'
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
              'hr_appli_id':fields.many2one('hr.applicant','Offer Letter Acceptance'),
              }    
class survey_test_line(osv.osv):
    _name='survey.test.line'
    _inherits = {'survey.request': 'request_id'}
    _inherit =  'mail.thread'
    _rec_name = 'request_id'
    _description = 'Technical Interview'
    _columns={
              'request_id': fields.many2one('survey.request','Request_id', ondelete='cascade', ),
              'aplicant_id':fields.many2one('hr.applicant'),
              'date_deadline':fields.date('Date'),
              'marks':fields.char('Scored',size=32),
############# it is used for the test configuration 
                'exam_name1':fields.char('Exam Name',size=64,readonly=True),
              'total_marks1':fields.integer('Total Marks',readonly=True),
              'min_score1':fields.integer('Minimum Marks',readonly=True),
              'scored':fields.integer('Scored'),
              'attach':fields.binary('Attachment'),
              'comment':fields.char('Comment',size=256),
              'user_id':fields.many2one('res.users','User Id'),
              }
    def survey_req_waiting_answer(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state': 'waiting_answer'}, context=context)
        return True
    def survey_req_done(self, cr, uid, ids, context=None):
        hr_eval_obj = self.pool.get('hr.applicant')
        for id in self.browse(cr, uid, ids, context=context):
            flag = False
            wating_id = 0
            if not id.aplicant_id.id:
                raise osv.except_osv(_('Warning!'),_("You cannot start evaluation without Appraisal."))
            records = hr_eval_obj.browse(cr, uid, [id.aplicant_id.id], context=context)[0].survey_ids
            for child in records:
                if child.state == "draft":
                    wating_id = child.id
                    continue
                if child.state != "done":
                    flag = True
            if not flag and wating_id:
                self.survey_req_waiting_answer(cr, uid, [wating_id], context=context)
        self.write(cr, uid, ids, { 'state': 'done'}, context=context)
        return True
    def action_print_survey(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record = self.browse(cr, uid, ids, context=context)
        record = record and record[0]
        context.update({'survey_id': record.survey_id.id, 'response_id': [record.response.id], 'response_no':0,})
        value = self.pool.get("survey").action_print_survey(cr, uid, ids, context=context)
        return value
class survey_request(osv.osv):
    _name='survey.request'
    _inherit='survey.request'
    
class mail_compose_message(osv.Model):
    _inherit = 'mail.compose.message'
    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('default_model') == 'hr.applicant' and context.get('default_res_id') and context.get('mark_so_as_sent'):
            context = dict(context, mail_post_autofollow=True)
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
class hr_employee(osv.osv):
    _inherit='hr.employee'
    def create(self, cr, uid, vals, context=None):
        super(hr_employee, self).create(cr, uid, vals, context=context)
        start= self.pool.get('ir.sequence').get(cr, uid, 'hr.employee') or '/'
        val1=int(start)
        seq=val1+105
        from datetime import datetime
        date = datetime.now()
        today=date.today()
        days=date.day
        month=date.month
        year=date.year
        fraction_year=year%100
        get_seq= 'S'+''+str(seq)+''+str(month)+''+str(fraction_year)
        vals['identification_id']=get_seq
        return super(hr_employee, self).create(cr, uid, vals, context=context)

