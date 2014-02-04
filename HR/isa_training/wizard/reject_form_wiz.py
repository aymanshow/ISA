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

    _columns={
              'name_id':fields.many2one('hr.employee','Employee Name',readonly=True),
              'requestion_id1':fields.char('Employee Id',readonly=True),
              'department':fields.many2one('hr.department','Department',readonly=True),
              'training_state': fields.selection(AVAILABLE_STATES, 'States',help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
              'comment':fields.text('Comment'),
              }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        applicant_ids = context.get('active_ids')
        res = super(rejected_form_training, self).default_get(cr, uid, fields, context=context)
        if applicant_ids:
            applicant_obj=self.pool.get('employee.training1').browse(cr ,uid ,applicant_ids[0])
            
            st_name=applicant_obj.emp_name_id.id
            
            subject_id=applicant_obj.emp_id
            
            req_id=applicant_obj.department_id.id
            
            stage_id=applicant_obj.training_state
            
            res.update({'name_id': st_name})
            res.update({'requestion_id1': req_id})
            res.update({'training_state': stage_id})
            res.update({'department': req_id})
        return res
    
    def create_record1(self, cr, uid, ids, context=None):
         res={} 
         applicant_ids = context.get('active_ids')  
         value1 = self.pool.get('employee.training1')

         mod_obj = self.pool.get('ir.model.data')
         record_id11=value1.search(cr ,uid ,[('training_state','=','refuse')])
         obj=value1.browse(cr,uid,record_id11[0])
         record= value1.browse(cr,uid,record_id11,context=context)

         wiz_obj=self.pool.get('employee.training1').browse(cr,uid,applicant_ids[0])
         self.write(cr, uid, ids,{'name_id':wiz_obj.emp_name_id.id,
                                  'requestion_id1':wiz_obj.emp_id,
                                  'partner_name':wiz_obj.department_id.id,
                                  'training_state':'refuse',
                                                         } ,context=context)
         return res
        

    
   
   