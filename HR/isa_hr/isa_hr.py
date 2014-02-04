from osv import osv
from osv import fields
import time
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext

class drishti_hr(osv.osv):
    _name = 'drishti.hr'
    _rec_name="unique_id"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _desc='drishti.hr'
    def create(self, cr, uid, vals, context={}):
        if (not 'unique_id' in vals) or (vals['unique_id'] == False):
                vals['unique_id'] = self.pool.get('ir.sequence').get(cr, uid, 'drishti.hr')
        return super(drishti_hr, self).create(cr, uid, vals, context)
    
    def action_quotation_send(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'isa_hr', 'drishti.hr')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'drishti.hr',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
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
    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'})
        return True
    def action_cancel(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True
    def _get_id(self,cr,uid,c):
         res=0
         department_id=False
         res=self.pool.get('hr.employee').search(cr,uid,[('user_id','=',uid)])
         if not res:
            raise osv.except_osv(('Warning !'),('please configure the employee related user and its department')) 
         else:
             department_id=self.pool.get('hr.employee').browse(cr,uid,res[0]).department_id.id
         return department_id
    _columns = {
	                'name': fields.char('Subject', size=128),
                    'number_of_recruitment':fields.integer('Number of Recruitment',required=True),
                    'department_id': fields.many2one('hr.department', 'Department',readonly=True),
                    'designation':fields.many2one('hr.job','Designation'),
                    'category_ids': fields.many2many('hr.employee.category', 'employee_category_relation', 'emp_id', 'category_id', 'Job Type'),
                   'joining_date':fields.date('Expected Joining Date'),
                   'job_description_ids':fields.one2many('job.description','job_id','Job Description'), 
                   'other':fields.text('Other Information'), 
                   'unique_id':fields.char('Requisition Id',readonly=True),
                   'year_exp':fields.date('Experience'),
                   'qualification_ids':fields.many2many('job.qualification','qualification_rel','name','course_id',' Required Qualification'), 
                    'emp_id':fields.many2one('res.users','Employee Id',readonly=True),
                   'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of stages."),
                   'state': fields.selection([('draft', 'New'),('waiting', 'Pending'),('confirmed', 'Process'),('done', 'Done'),('cancel', 'Cancel')], 'Status', readonly=True, select=True,
                 help= "* New: When the stock move is created and not yet confirmed.\n"\
                       "* Pending: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"\
                       "*Process: This state is reached when the recruitmentt is going on \n"\
                       "* Done: When the recruitment is processed, the state is \'Done\'."),
                'picking_id': fields.char( 'Reference', select=True,states={'done': [('readonly', True)]}),
                'hr_employee_id':fields.many2one('hr.employee','Employee'),
                 }
    _defaults = {
                 'state':'draft',
                 'sequence': 1,
                 'department_id':lambda self,cr,uid,c:self._get_id(cr, uid,c),
                 'emp_id': lambda obj, cr, uid, context: uid
                 }
    def action_submit(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        if obj.number_of_recruitment == 0:
            raise osv.except_osv(('Warning !'),('Please fill the Number of Recruitment'))
        else:
            self.write(cr, uid, ids, {'state': 'waiting'})
        return True
    def action_approve(self,cr,uid,ids,context=None):
        hr_job_obj=self.pool.get('hr.job')
        obj=self.browse(cr,uid,ids[0])
        hr_job_id=hr_job_obj.search(cr,uid,[('name','=',obj.designation.name),('state','=','open'),('department_id','=',obj.department_id.id)])
        if not hr_job_id:
            raise osv.except_osv(('Warning !'),('For this designation recruitment is being process.'))
        else:
            hr_job_obj.write(cr, uid,hr_job_id[0],{'name':obj.designation.name,'no_of_recruitment':obj.number_of_recruitment,'department_id':obj.department_id.id,'state': 'recruit','description':obj.other}, context = context) 
            hr_job_obj.job_recruitement(cr,uid,hr_job_id)
            self.write(cr, uid, ids, {'state':'confirmed'})
        return True
    
    def onchange_employee_id(self, cr, uid, ids, emp_id, context=None):
            res={}
            flag=0
            employee_obj = self.pool.get('hr.employee')
            user_obj=self.pool.get('res.users')
            
            line= employee_obj.browse(cr,uid,emp_id)
            res={
                 'department_id':line.department_id.id
                 }
            return {'value': res}
drishti_hr()

class job_description(osv.osv):
    _name='job.description'
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'job_description':fields.text('Job Description'),
              'serial_num' : fields.function(get_serial_no,type='integer',string='Sr.No'),
              'job_id':fields.many2one('drishti.hr','Drishti Hr'),          
              }
   
    
class job_qualification(osv.osv):
    _name='job.qualification'
    _columns={
              'name':fields.char('Course Name'),
              'course_id':fields.many2one('hr.recruitment.degree','Course'),
              
             }
class hr_job(osv.osv):
        _name='hr.job'
        _inherit='hr.job'
        _columns={
               'unique_id1':fields.many2one('drishti.hr','Requisition Id',domain=[('state', '=', 'confirmed')],help='Enter the Unique Id which is approved.')
                 }
        def onchange_unique_id(self,cr,uid,ids,unique_id1,context=None):
            res={}
            info=''
            drishtihr_obj=self.pool.get('drishti.hr')
            hrjob_obj=self.pool.get('hr.job')
            jobdesc_obj=self.pool.get('job.description')
            jobquali_obj=self.pool.get('job.qualification')
            drishtihr_ids=drishtihr_obj.search(cr ,uid ,[('state','=','confirmed')])
            line= drishtihr_obj.browse(cr,uid,unique_id1)
            if  unique_id1 in drishtihr_ids:
                for result in line.job_description_ids:
                         info=str(result.serial_num) +'-'+ result.job_description + ',  '
                res ={
                      'name':line.name,
                      'no_of_recruitment':line.number_of_recruitment,
                      'department_id':line.department_id.id,
                      'description':line.other,
                      'requirements':info
                      } 
            return {'value': res}
#This method is used for the sending mails 
        def action_quotation_send(self, cr, uid, ids, context=None):
            test=[]
            email_template_obj = self.pool.get('email.template')
            ir_model_data = self.pool.get('ir.model.data')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','hr.job')], context=context)
            if not template_ids:
                raise osv.except_osv(
                                _('Error!'),
                                _('Please Create the template for this module'))
            if template_ids:
                    values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
                    email_obj=self.browse(cr,uid,ids[0])
                    try:
                        compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                    except ValueError:
                        compose_form_id = False
                    if not email_obj.no_of_recruitment:
                         raise osv.except_osv(
                                _('Error!'),
                                _('Please Invalid the Employee Unique Id.PLease Inform the Department and fill the all field in the requestion form'))
                    if  email_obj.no_of_employee:
                         email_obj.no_of_employee=0.0
                    mail_mail_obj = self.pool.get('mail.mail')
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
