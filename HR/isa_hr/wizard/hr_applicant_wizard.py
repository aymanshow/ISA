from osv import osv
from osv import fields
import time
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext

class rejected_form(osv.osv):
    _name='rejected.form'
    _columns={
              'name_id':fields.char('Subject',readonly=True),
              'requestion_id1':fields.char('Applicant Id',readonly=True),
              'partner_name':fields.char('Applicant',readonly=True),
              'stage1':fields.selection([
                                            ('draft', 'Initial Qualification'),
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
                                            
                                        ],'State'),
              'comment':fields.text('Comment'),
              }
# function for cancel the button in the wizard
    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
# function for getting the default value of the stage in the wizard
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        
        applicant_ids = context.get('active_ids')
        res = super(rejected_form, self).default_get(cr, uid, fields, context=context)
        if applicant_ids:
            applicant_obj=self.pool.get('hr.applicant').browse(cr ,uid ,applicant_ids[0])
            st_name=applicant_obj.partner_name
            subject_id=applicant_obj.name
            req_id=applicant_obj.candidate_id
            stage_id=applicant_obj.state
            res.update({'partner_name': st_name})
            res.update({'requestion_id1': req_id})
            res.update({'stage1': stage_id})
            res.update({'name_id': subject_id})
        return res
#this method is used for wizard action for save button cancel    
    def create_record2(self,cr,uid,ids,context=None):
         res={} 
         applicant_ids = context.get('active_ids')  
         value1 = self.pool.get('hr.recruitment.stage')
         hr_appli_obj=self.pool.get('hr.applicant')
         mod_obj = self.pool.get('ir.model.data')
         record_id11=value1.search(cr ,uid ,[('state','=','cancel')],context=context)
         obj=hr_appli_obj.browse(cr,uid,record_id11[0])
         record= value1.browse(cr,uid,record_id11,context=context)
         hr_appli_obj.write(cr, uid, applicant_ids[0],{'stage_id':obj.id})
         wiz_obj=self.pool.get('hr.applicant').browse(cr,uid,applicant_ids[0])
         if not wiz_obj.name:
             raise osv.except_osv(_('Warning!'), _('You must define the applicant name.'))
         else:
             self.write(cr, uid, ids,{'name_id':wiz_obj.name,
                                      'requestion_id1':wiz_obj.candidate_id,
                                      'partner_name':wiz_obj.partner_name,
                                      'stage1':wiz_obj.state,
                                       } ,context=context)
         return res
           
   
   