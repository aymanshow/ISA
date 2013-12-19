from osv import osv
from osv import fields
import time
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext
AVAILABLE_STATES = [
    ('draft', 'New'),
    ('approval', 'Approval'),
    ('legal_process', 'Legal Process'),
    ('payment', 'Payment'),
    ('awaiting_certificate', 'Awaiting Certificate'),
    ('pending', 'Pending'),
    ('done', 'Certified'),
    ('refuse', 'Rejected'),
]
class rejected_form_training(osv.osv_memory):
    _name='rejected.form.training'
#     _inherit='hr.applicant'
    _columns={
              'name_id':fields.many2one('hr.employee','Employee Name',readonly=True),
              'requestion_id1':fields.char('Employee Id',readonly=True),
              'department':fields.many2one('hr.department','Department',readonly=True),
              'training_state': fields.selection(AVAILABLE_STATES, 'States',help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
              'comment':fields.text('Comment'),
              }
# # function for cancel the button in the wizard
#     def action_cancel(self, cr, uid, ids, context=None):
#         return {'type': 'ir.actions.act_window_close'}
# # function for getting the default value of the stage in the wizard
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        applicant_ids = context.get('active_ids')
        res = super(rejected_form_training, self).default_get(cr, uid, fields, context=context)
        if applicant_ids:
            applicant_obj=self.pool.get('employee.training1').browse(cr ,uid ,applicant_ids[0])
            print'===applicant_ids======',applicant_obj
            st_name=applicant_obj.emp_name_id.id
            print'======st_name=====',st_name
            subject_id=applicant_obj.emp_id
            print'=======subject_id=====',subject_id
            req_id=applicant_obj.department_id.id
            print'========req_id====',req_id
            stage_id=applicant_obj.training_state
            print'=====state=====',stage_id
            res.update({'name_id': st_name})
            res.update({'requestion_id1': req_id})
            res.update({'training_state': stage_id})
            res.update({'department': req_id})
        return res
#this method is used for wizard action for save button cancel    
    def create_record1(self, cr, uid, ids, context=None):
         res={} 
         applicant_ids = context.get('active_ids')  
         value1 = self.pool.get('employee.training1')
#          hr_appli_obj=self.pool.get('employee.training1')
         mod_obj = self.pool.get('ir.model.data')
         record_id11=value1.search(cr ,uid ,[('training_state','=','refuse')])
         obj=value1.browse(cr,uid,record_id11[0])
         record= value1.browse(cr,uid,record_id11,context=context)
#          value1.write(cr, uid, applicant_ids[0],{'stage_id':obj.id})
         wiz_obj=self.pool.get('employee.training1').browse(cr,uid,applicant_ids[0])
         self.write(cr, uid, ids,{'name_id':wiz_obj.emp_name_id.id,
                                  'requestion_id1':wiz_obj.emp_id,
                                  'partner_name':wiz_obj.department_id.id,
                                  'training_state':'refuse',
                                                         } ,context=context)
         return res
        

    
   
   