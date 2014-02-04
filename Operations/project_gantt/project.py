from osv import osv
from osv import fields
import openerp.addons.decimal_precision as dp
import time
import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _


class mail_compose_message(osv.TransientModel):
    _inherit='mail.compose.message'
      
    def send_mail(self, cr, uid, ids, context=None):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """
        for z in self.browse(cr, uid, ids, context=None):
            main_form_id = z.res_id
        if context is None:
            context = {}
        ir_attachment_obj = self.pool.get('ir.attachment')
        active_ids = context.get('active_ids')
        is_log = context.get('mail_compose_log', False)
 
        for wizard in self.browse(cr, uid, ids, context=context):
            mass_mail_mode = wizard.composition_mode == 'mass_mail'
            active_model_pool_name = wizard.model if wizard.model else 'mail.thread'
            active_model_pool = self.pool.get(active_model_pool_name)
 
            # wizard works in batch mode: [res_id] or active_ids
            res_ids = active_ids if mass_mail_mode and wizard.model and active_ids else [wizard.res_id]
            for res_id in res_ids:
                # mail.message values, according to the wizard options
                post_values = {
                    'subject': wizard.subject,
                    'body': wizard.body,
                    'parent_id': wizard.parent_id and wizard.parent_id.id,
                    'partner_ids': [partner.id for partner in wizard.partner_ids],
                    'attachment_ids': [attach.id for attach in wizard.attachment_ids],
                }
                # mass mailing: render and override default values
                if mass_mail_mode and wizard.model:
                    email_dict = self.render_message(cr, uid, wizard, res_id, context=context)
                    post_values['partner_ids'] += email_dict.pop('partner_ids', [])
                    post_values['attachments'] = email_dict.pop('attachments', [])
                    attachment_ids = []
                    for attach_id in post_values.pop('attachment_ids'):
                        new_attach_id = ir_attachment_obj.copy(cr, uid, attach_id, {'res_model': self._name, 'res_id': wizard.id}, context=context)
                        attachment_ids.append(new_attach_id)
                    post_values['attachment_ids'] = attachment_ids
                    post_values.update(email_dict)
                # post the message
                subtype = 'mail.mt_comment'
                if is_log:  # log a note: subtype is False
                    subtype = False
                elif mass_mail_mode:  # mass mail: is a log pushed to recipients, author not added
                    subtype = False
                    context = dict(context, mail_create_nosubscribe=True)  # add context key to avoid subscribing the author
                msg_id = active_model_pool.message_post(cr, uid, [res_id], type='comment', subtype=subtype, context=context, **post_values)
                # mass_mailing: notify specific partners, because subtype was False, and no-one was notified
                if mass_mail_mode and post_values['partner_ids']:
                    self.pool.get('mail.notification')._notify(cr, uid, msg_id, post_values['partner_ids'], context=context)
                 
                search_project_form = self.pool.get('project.project').search(cr, uid, [('id', '=', main_form_id)])
                 
                for k in self.pool.get('project.project').browse(cr,uid,search_project_form):
                    sr_upload_doc = k.sr_upload
                    sr_approver = k.sr_id
                    sr_state = k.state_for_sr
                     
                    ko_upload_doc = k.ko_upload
                    ko_approver = k.ko_id
                    ko_state = k.state_for_ko
                     
                    pc_upload_doc = k.pc_upload
                    pc_approver = k.pc_id
                    pc_state = k.state_for_pc
                     
                    fd_upload_doc = k.fd_upload
                    fd_approver = k.fd_id
                    fd_state = k.state_for_fd
                     
                    if sr_approver and sr_upload_doc:
                        self.pool.get('project.project').write(cr,uid,k.id,{'state_for_sr':'sent_for_approval'})
                         
                    if ko_approver and ko_upload_doc:
                        self.pool.get('project.project').write(cr,uid,k.id,{'state_for_ko':'sent_for_approval'})
                         
                    if pc_approver and pc_upload_doc:
                        self.pool.get('project.project').write(cr,uid,k.id,{'state_for_pc':'sent_for_approval'})
                         
                    if fd_approver and fd_upload_doc:
                        self.pool.get('project.project').write(cr,uid,k.id,{'state_for_fd':'sent_for_approval'})
                 
                
        return {'type': 'ir.actions.act_window_close'}











class project_project(osv.osv):
    _inherit='project.project'
    
    def view_budget(self,cr,uid,ids,context):
       res={}
       list=[]
       obj=self.browse(cr,uid,ids[0])
       if obj.budget_id:
           list.append(obj.budget_id.id)
           
           res = {
                   'domain': ([('id', 'in', list)]),
                   'view_type': 'form',
                   'view_mode': 'form',
                   'res_model': 'crossovered.budget',
                   'target':'current',
                   'nodestroy': True,
                   'type': 'ir.actions.act_window',
                   'name' : 'Budgets',
                   'res_id': list[0]
                   }
       else:
           res = {
                   'domain': ([('id', 'in', list)]),
                   'view_type': 'form',
                   'view_mode': 'tree,form',
                   'res_model': 'crossovered.budget',
                   'target':'current',
                   'nodestroy': True,
                   'type': 'ir.actions.act_window',
                   'name' : 'Budgets',
                   'res_id': list
                   }
       return res
    
    def _data_set_kick(self, cr, uid, id, name, value, arg, context=None):
        # We dont handle setting data to null
        if not value:
            return True
        if context is None:
            context = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        file_size = len(value.decode('base64'))
        if location:
            attach = self.browse(cr, uid, id, context=context)
            if attach.store_fname:
                self._file_delete(cr, uid, location, attach.store_fname)
            fname = self._file_write(cr, uid, location, value)
            super(project_project, self).write(cr, uid, [id], {'store_fname': fname, 'file_size': file_size}, context=context)
        else:
            super(project_project, self).write(cr, uid, [id], {'db_datas': value, 'file_size': file_size}, context=context)
        return True
    
    def _data_get_document(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        bin_size = context.get('bin_size')
        for attach in self.browse(cr, uid, ids, context=context):
            if location and attach.datas_project_charter:
                result[attach.id] = self._file_read(cr, uid, location, attach.datas_project_charter, bin_size)
            else:
                result[attach.id] = attach.db_datas1
        return result
    
    def _data_set_document(self, cr, uid, id, name, value, arg, context=None):
        # We dont handle setting data to null
        if not value:
            return True
        if context is None:
            context = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        file_size = len(value.decode('base64'))
        if location:
            attach = self.browse(cr, uid, id, context=context)
            if attach.store_fname_doc:
                self._file_delete(cr, uid, location, attach.store_fname_doc)
            fname = self._file_write(cr, uid, location, value)
            super(project_project, self).write(cr, uid, [id], {'store_fname_doc': fname, 'file_size1': file_size}, context=context)
        else:
            super(project_project, self).write(cr, uid, [id], {'db_datas1': value, 'file_size1': file_size}, context=context)
        return True
    
    def _data_get_kick(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        bin_size = context.get('bin_size')
        for attach in self.browse(cr, uid, ids, context=context):
            if location and attach.store_fname:
                result[attach.id] = self._file_read(cr, uid, location, attach.store_fname, bin_size)
            else:
                result[attach.id] = attach.db_datas
        return result
    
    _columns={
              'pnl':fields.many2one('pnl.order','Related Pnl'),
              'weekly_report':fields.binary('Weekly Status Report'),
              'weekly_line':fields.one2many('weekly.details','weekly_id'," ", size=124),
              'certificate':fields.binary('Certificate to be sent to the customer'),
              'final_presentation':fields.binary('Final Presentation'),
              'administrative_closure':fields.binary('Administrative Closure'),
              'technical_closure':fields.binary('Technical Closure'),
              'solution_review':fields.binary('Solution Review Comments'),
              'project':fields.binary('Project Charter'),
              'finance_document':fields.binary('Finance Documents'),
              'solution':fields.binary('Solution Review'),
              'training_plan':fields.binary('Training Plan'),
              'technical_plan':fields.binary('Technical Plan'),
              'implementation_plan':fields.binary('Master Implementation Plan'),
              'budget_id':fields.many2one('crossovered.budget','Budgets'),
              'state': fields.selection([
                        ('draft','New'),('initiate','Initiate'),
                        ('plan','Planning'),('execute','Execution'),
                        ('close','Closure'),('sign_off','Signed off'),
                         ('canceled', 'Canceled'),
                         ], 'Status', required=True,track_visibility='onchange'),
              'risk_id':fields.many2one('risk.management','Risk Management'),
              'request_id':fields.many2one('change.request','Change Request'),
              ###New Code
              'filename1': fields.char('File Name',size=256),
              'filename2': fields.char('File Name',size=256),
              'filename3': fields.char('File Name',size=256),
              'filename4': fields.char('File Name',size=256),
              'sr_id':fields.many2one('res.users','Select Approver'),
              'ko_id':fields.many2one('res.users','Select Approver'),
              'pc_id':fields.many2one('res.users','Select Approver'),
              'fd_id':fields.many2one('res.users','Select Approver'),
              
              'sr_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              'ko_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              'pc_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              'fd_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              
              'sr_upload': fields.binary('Upload File1'),
              'ko_upload': fields.binary('Upload File2'),
              'pc_upload': fields.binary('Upload File3'),
              'fd_upload': fields.binary('Upload File4'),
              
              'sr_partner':fields.many2one('res.partner', 'Partner'),
              
              'state_for_sr': fields.selection([ 
                                       ('new','New'),
                                       ('sent_for_approval', 'Sent For Approval'),
                                       ('approved', 'Approved'),],'Status',readonly=True,),
              'state_for_ko': fields.selection([
                                       ('new','New'),
                                       ('sent_for_approval', 'Sent For Approval'),
                                       ('approved', 'Approved'),],'Status',readonly=True,),
              'state_for_pc': fields.selection([
                                       ('new','New'),
                                       ('sent_for_approval', 'Sent For Approval'),
                                       ('approved', 'Approved'),],'Status',readonly=True,),
              'state_for_fd': fields.selection([
                                       ('new','New'),
                                       ('sent_for_approval', 'Sent For Approval'),
                                       ('approved', 'Approved'),],'Status',readonly=True,),
               
               
              'comments_sr':fields.text('Remarks'),
              'comments_ko':fields.text('Remarks'),
              'comments_pc':fields.text('Remarks'),
              'comments_fd':fields.text('Remarks'),                         
              
              
              
              'comment_datas':fields.text('Remarks'),
              'store_fname': fields.char('Stored Filename', size=256),
              'datas_project_charter_fname': fields.char('File Name',size=256),
              'datas_project_charter': fields.function(_data_get_document, fnct_inv=_data_set_document, string='Upload Project Document', type="binary", nodrop=True),
              'approve_project_charter_id':fields.many2one('res.users','Select Approver'),
              'comment_project':fields.text('Remarks'),
              'datas_finance_document_fname': fields.char('File Name',size=256),
              'datas_finance_document': fields.function(_data_get_document, fnct_inv=_data_set_document, string='Upload Finance Document', type="binary", nodrop=True),
              'approve_finance_document_id':fields.many2one('res.users','Select Approver'),
              'comment_finance':fields.text('Remarks'),
              'db_datas': fields.binary('Database Data'),
              'db_datas1': fields.binary('Database Data'),
              'store_fname_doc': fields.char('Stored Filename', size=256),
              'file_size': fields.integer('File Size'),
              'file_size1': fields.integer('File Size'),
              
              }
    _defaults={
               'state':'draft'
               
               }
    def view_po(self,cr,uid,ids,context):
        res={}
        list=[]
        obj=self.browse(cr,uid,ids[0])
        if obj.pnl:
            for val in obj.pnl.line_ids:
                list.append(val.quotation_id.id)
            res = {
                        'domain': ([('id', 'in', list)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'purchase.order',
                        'target':'current',
                        'nodestroy': True,
                        'type': 'ir.actions.act_window',
                        'name' : 'Purchase Order',
                        'res_id': list
                    }
        else:
            res={
                'domain': ([('id', 'in', list)]),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'target':'current',
                'nodestroy': True,
                'type': 'ir.actions.act_window',
                'name' : 'Purchase Order',
                'res_id': list
                 }
        return res
    def view_risk(self,cr,uid,ids,context):
        res={}
        list=[]
        obj=self.browse(cr,uid,ids[0])
        if obj.risk_id:
            list.append(obj.risk_id.id)
            res = {
                    'domain': ([('id', 'in', list)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'risk.management',
                    'target':'current',
                    'nodestroy': True,
                    'type': 'ir.actions.act_window',
                    'name' : 'Risk Management',
                    'res_id': list[0]
                    }
        else:
            res = {
                    
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'risk.management',
                    'target':'current',
                    'view_id': list,
                    'nodestroy': True,
                    'type': 'ir.actions.act_window',
                    'name' : 'Risk Management',
                   
                    }
        return res
    def change_request(self,cr,uid,ids,context):
        res={}
        list=[]
        obj=self.browse(cr,uid,ids[0])
        if obj.request_id:
            list.append(obj.request_id.id)
            res = {
                    'domain': ([('id', 'in', list)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'change.request',
                    'target':'current',
                    'nodestroy': True,
                    'type': 'ir.actions.act_window',
                    'name' : 'Change Request',
                    'res_id': list[0]
                    }
        else:
            res = {
                    
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'change.request',
                    'target':'current',
                    'nodestroy': True,
                    'type': 'ir.actions.act_window',
                    'name' : 'Change Request',
                    
                    }
        return res
    def onchange_sr_approve_id(self, cr, uid, ids, sr_approve_id):
            v={}
            if sr_approve_id:
               partner1=self.pool.get('hr.employee').browse(cr, uid, sr_approve_id)
               v['sr_id']=partner1.user_id.id
               
            
            return {'value':v}
        
    def onchange_ko_approve_id(self, cr, uid, ids, ko_approve_id):
            v={}
            if ko_approve_id:
               partner2=self.pool.get('hr.employee').browse(cr, uid, ko_approve_id)
               v['ko_id']=partner2.user_id.id
               
            
            return {'value':v}
        
    def onchange_pc_approve_id(self, cr, uid, ids, pc_approve_id):
            v={}
            if pc_approve_id:
               partner3=self.pool.get('hr.employee').browse(cr, uid, pc_approve_id)
               v['pc_id']=partner3.user_id.id
               
            return {'value':v}
        
    def onchange_fd_approve_id(self, cr, uid, ids, fd_approve_id):
            v={}
            if fd_approve_id:
               partner4=self.pool.get('hr.employee').browse(cr, uid, fd_approve_id)
               v['fd_id']=partner4.user_id.id
               
            return {'value':v}
    
    def set_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'draft'}, context=context)    

    def start_project(self,cr,uid,ids,context):
        self.write(cr,uid,ids[0],{'state':'initiate'})
        return True
    
    def planning(self,cr,uid,ids,context):
        obj=self.browse(cr,uid,ids[0])
        if not (obj.sr_upload and obj.ko_upload and obj.pc_upload and obj.fd_upload):
            raise osv.except_osv(_("Warning!"), _("Upload All the required documents First"))
        else:
            self.write(cr,uid,obj.id,{'state':'plan'})
        return True
    
    def execute(self,cr,uid,ids,context):
        obj=self.browse(cr,uid,ids[0])
        if not (obj.training_plan and obj.technical_plan and obj.implementation_plan):
            raise osv.except_osv(_("Warning!"), _("Upload All the required documents First"))
        else:
            
            self.write(cr,uid,ids[0],{'state':'execute'})
            for val in obj.tasks:
                self.pool.get('project.task').write(cr,uid,val.id,{'state1':'execute'})
            
        return True
    
    
    def send_mail_sr(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.sr_upload
            approver_name = x.sr_id.id
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','sr_id')], context=context)
            
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','sr_id')], context=context)
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            
            ctx = dict(context)
            
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
        else:
            raise osv.except_osv(
                    _('Error!'),
                    _('You cannot send mail until you select the Approver and upload the required document'))
            

        return True
    
    def send_mail_ko(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.ko_upload
            approver_name = x.ko_id.id
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','ko_id')], context=context)
            
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','ko_id')], context=context)
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
        else:
            raise osv.except_osv(
                    _('Error!'),
                    _('You cannot send mail until you select the Approver and upload the required document'))
        return True

    
    def send_mail_pc(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.pc_upload
            approver_name = x.pc_id.id
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','pc_id')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','pc_id')], context=context)
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
             
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
        else:
            raise osv.except_osv(
                    _('Error!'),
                    _('You cannot send mail until you select the Approver and upload the required document'))
            

        return True
    
    def send_mail_fd(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.fd_upload
            approver_name = x.fd_id.id
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','fd_id')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','fd_id')], context=context)
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
             
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
        else:
            raise osv.except_osv(
                    _('Error!'),
                    _('You cannot send mail until you select the Approver and upload the required document'))
            

        return True
    
    
    
    def approve_by_admin_sr(self,cr,uid,ids,context=None):
            self.write(cr, uid, ids, {'state_for_sr': 'approved'})
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','sr_approve_id')], context=context)
            
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','sr_approve_id')], context=context)
            
             
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
            
            
            return True
    
    def approve_by_admin_ko(self,cr,uid,ids,context=None):
            self.write(cr, uid, ids, {'state_for_ko': 'approved'})
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','ko_approve_id')], context=context)
            
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','ko_approve_id')], context=context)
            
             
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
            
            
            return True
    
    def approve_by_admin_pc(self,cr,uid,ids,context=None):
            self.write(cr, uid, ids, {'state_for_pc': 'approved'})
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','pc_approve_id')], context=context)
            
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','pc_approve_id')], context=context)
            
             
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
            
            
            return True
    
    def approve_by_admin_fd(self,cr,uid,ids,context=None):
            self.write(cr, uid, ids, {'state_for_fd': 'approved'})
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','fd_approve_id')], context=context)
            
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project'),('model_object_field.name', '=','fd_approve_id')], context=context)
            
             
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'project.project',
                'default_res_id': ids[0],
                'default_use_template': bool(template_ids),
                'default_template_id': template_ids[0],
                'default_composition_mode': 'comment',
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
            
            
            return True
    

    def set_done(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state':'close'})
        
    def sign_off(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        if not (obj.certificate and obj.final_presentation and obj.administrative_closure and obj.technical_closure):
            raise osv.except_osv(_("Warning!"), _("Upload All the required documents First"))
        else:
            
            self.write(cr,uid,ids,{'state':'sign_off'})
        
    
        
    
class weekly_details(osv.osv):
    _name = "weekly.details"
    _description = "Weekly Status Reports"
    _columns = {
        'weekly_id': fields.many2one('project.project','Weekly Status Report No.', size=124),
        'weekly_report':fields.binary('Weekly Status Report'),
        'remarks':fields.text('Remarks'),
        'date':fields.date('Date'),

        }    


    
class project_task(osv.osv):
    _inherit='project.task'
    _columns={
              'parent_id':fields.many2one('project.task','Depends On'),
              'date_close_actual':fields.date('Estimated End Date'),
              'date_open_actual':fields.date('Estimated Start Date'),
              'days_delay':fields.integer('Delay'),
              'days_needed':fields.integer('Days Needed To Finish the task'),
              'state1':fields.selection([('draft','Draft'),('execute','Execute')]),
              }
    _defaults={
               'state1':'draft',
               
               }
    def onchange_closing(self,cr,uid,ids,start,end,days_needed,delay,context=None):
        res={}
        end_date=datetime.date.today()
        if end:
            
            end_date==datetime.datetime.strptime(end,'%Y-%m-%d %H:%M:%S').date()
            if end_date:
                date_open_next=end_date + relativedelta(days = +delay)
            else:
                date_open_next=''
        date_close_next=date_open_next+relativedelta(days = +days_needed)
        if date_open_next:
            res={
                 'date_open_actual':str(date_open_next),
                 'date_close_actual':str(date_close_next),
                 }
            return {'value':res}
        return res
    
    def action_close(self, cr, uid, ids, context=None):
        """ This action closes the task
        """
        obj=self.browse(cr,uid,ids[0])
        depend_id=self.search(cr,uid,[('parent_id','=',obj.id),('state','!=','done')])
        if depend_id:
            raise osv.except_osv(_("Warning!"), _("Dependent task still open.\nPlease cancel or complete the task which depend on."))
        else:
            task_id = len(ids) and ids[0] or False
            self._check_child_task(cr, uid, ids, context=context)
            if not task_id: return False
        return self.do_close(cr, uid, [task_id], context=context)
    
class risk_management(osv.osv):
    _name='risk.management'
    _columns={
              'project_id':fields.many2one('project.project','Project'),
              'date_start':fields.date('Start Date'),
              'date_end':fields.date('End Date'),
              'risk_lines':fields.one2many('risk.line','risk_id','Risk Lines'),
              'state':fields.selection([('open','Open'),('close','Closed'),],'Status',required=True),
              }
    _defaults={
               'state':'open',
               }
    def default_get(self, cr, uid, fields, context=None):
        res = super(risk_management, self).default_get(cr, uid, fields, context=context)
        act_id=context.get('active_id')
        if context.get('active_id'):
            tomerge = set([int(context['active_id'])])
            obj = self.pool.get('project.project').browse(cr, uid, int(context['active_id']), context=context)
            res.update({'project_id' : obj.id,'date_start':obj.date_start,'date_end':obj.date,
                        })
 
        return res
    def validate(self,cr,uid,ids,context):
        res={}
        self.write(cr,uid,ids,{'state':'close'})
        return True
    def create(self, cr, uid, vals, context=None):
        res={}
        project_id=vals['project_id']
        if project_id:
            res=super(risk_management, self).create(cr, uid, vals, context=context)
            self.pool.get('project.project').write(cr,uid,project_id,{'risk_id':res})
        return res

class risk_line(osv.osv):
    _name='risk.line'
    _columns={
              'risk_id':fields.many2one('risk.management','Risk ID'),
              'description':fields.char('Description'),
              'probability':fields.char('Probability'),
              'impact':fields.char('Impact On Project'),
              'exposure':fields.char('Exposure'),
              'status':fields.selection([('active','Active'),('pending','Pending'),('close','Closed')],'Status',required=True),
              'plan':fields.char('Mitigation Plan'),
              'progress':fields.char('Work Progress'),
              }
    

class change_request(osv.osv):
    _name='change.request'
    _columns={
              'project_id':fields.many2one('project.project','Project'),
              'date_start':fields.date('Start Date'),
              'date_end':fields.date('End Date'),
              'new_date_start':fields.date('New Start Date'),
              'new_date_end':fields.date('New End Date'),
              'state':fields.selection([('draft','New'),('pending','Pending'),('approve','Approved'),('change','Changed'),('cancel','Cancelled')],'Status'),
              'pnl':fields.many2one('pnl.order','P&L'),
              }
    
    _defaults={
               'state':'draft',
               
               }
    def create(self, cr, uid, vals, context=None):
        res={}
        project_id=vals['project_id']
        if project_id:
            res=super(change_request, self).create(cr, uid, vals, context=context)
            self.pool.get('project.project').write(cr,uid,project_id,{'request_id':res})
        return res
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(change_request, self).default_get(cr, uid, fields, context=context)
        act_id=context.get('active_id')
        if context.get('active_id'):
            tomerge = set([int(context['active_id'])])
            obj = self.pool.get('project.project').browse(cr, uid, int(context['active_id']), context=context)
            res.update({'project_id' : obj.id,'date_start':obj.date_start,'date_end':obj.date,'new_date_start':obj.date_start,'new_date_end':obj.date
                        })
        return res
        
        
       
    def send(self,cr,uid,ids,context):
        self.write(cr,uid,ids,{'state':'pending'})
        return True
    def cancel(self,cr,uid,ids,context):
        self.write(cr,uid,ids,{'state':'cancel'})
        return True
    def approve(self,cr,uid,ids,context):
        self.write(cr,uid,ids,{'state':'approve'})
        return True
    def validate(self,cr,uid,ids,context):
        obj=self.browse(cr,uid,ids[0])
        if obj.new_date_end:
            date_to=obj.new_date_end
        else:
            date_to=obj.date_end
        if obj.new_date_start:
            date_from=obj.new_date_start
        else:
            date_from=obj.date_start
        if obj.pnl.id:
            name=obj.pnl.name
            project_analytic_id=obj.project_id.analytic_account_id.id
            equip_dict = {'name': 'Products', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':project_analytic_id,}
            products_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'Cost of Goods Sold', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            cogs_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'CIF', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            cif_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'Consulting', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            consult_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)    
            equip_dict = {'name': 'Overheads', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            overheads_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
    
            equip_dict = {'name': 'Service', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':project_analytic_id,}
            services_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'Cost of Services', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':services_analytic_id,}
            cost_service_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            
            """Creation of Budget"""
            budget_dict = {'name':"Budget for: " + name ,
                           'code':name,
                           'date_from':date_from,
                           'date_to':date_to,
                           }
            budget_id = self.pool.get('crossovered.budget').create(cr, uid, budget_dict, context=context)
            
            """"Creation of analytic accounts and budget lines for Product section of the P&L.""" 
            equip_dict = {
                          'name': 'Revenue', 
                          'active': True, 
                          'type': 'normal', 
                          'parent_id':products_analytic_id,
                          }
            analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            budget_line_dict ={
                           'crossovered_budget_id': budget_id,
                           'analytic_account_id': analy_id,
                           'general_budget_id': 1,
                           'date_from': date_from, 
                           'date_to':date_to,
                           'planned_amount': obj.pnl.cogs_rev,
                           }
            self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            
            """P&L COGS, CIF and Consulting"""
            for vals in obj.pnl.line_ids:
                
                equip_dict = {'name': vals.name, 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':cogs_analytic_id,}
                analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                budget_line_dict ={
                                       'crossovered_budget_id': budget_id,
                                       'analytic_account_id': analy_id,
                                       'general_budget_id': 2,
                                       'date_from': date_from, 
                                       'date_to':date_to,
                                       'planned_amount': -  vals.quote_amt,
                                       }
                self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
                
                if vals.cif_amt:
                    equip_dict = {'name': vals.name + " CIF", 
                                  'active': True, 
                                  'type': 'normal', 
                                  'parent_id':cif_analytic_id,}
                    analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                    budget_line_dict ={
                                           'crossovered_budget_id': budget_id,
                                           'analytic_account_id': analy_id,
                                           'general_budget_id': 2,
                                           'date_from': date_from, 
                                           'date_to':date_to,
                                           'planned_amount': -vals.cif_amt,
                                           }
                    self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
                if vals.consultancy_amt:
                    equip_dict = {'name': vals.name + " Consulting", 
                                  'active': True, 
                                  'type': 'normal', 
                                  'parent_id':consult_analytic_id,}
                    analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                    budget_line_dict ={
                                           'crossovered_budget_id': budget_id,
                                           'analytic_account_id': analy_id,
                                           'general_budget_id': 2,
                                           'date_from': date_from, 
                                           'date_to':date_to,
                                           'planned_amount': -vals.consultancy_amt,
                                           }
                    self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
             
            for vals in obj.pnl.cogs_addl_costs:
                budget_line_ids = {}
                equip_dict = {'name': vals.name, 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':overheads_analytic_id,}
                analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                budget_line_dict ={
                                       'crossovered_budget_id': budget_id,
                                       'analytic_account_id': analy_id,
                                       'general_budget_id': 2,
                                       'date_from': date_from, 
                                       'date_to':date_to,
                                       'planned_amount': -vals.amount,
                                       }
                self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            
            """"Creation of analytic accounts and budget lines for Services section of the P&L.""" 
            equip_dict = {
                          'name': 'Revenue', 
                          'active': True, 
                          'type': 'normal', 
                          'parent_id':services_analytic_id,
                          }
            analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            budget_line_dict ={
                           'crossovered_budget_id': budget_id,
                           'analytic_account_id': analy_id,
                           'general_budget_id': 1,
                           'date_from': date_from, 
                           'date_to':date_to,
                           'planned_amount': obj.pnl.serv_rev,
                           }
            self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            
            for vals in obj.pnl.serv_line:
                budget_line_ids = {}
                equip_dict = {'name': vals.product_id.name, 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':cost_service_analytic_id,}
                analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                budget_line_dict ={
                                       'crossovered_budget_id': budget_id,
                                       'analytic_account_id': analy_id,
                                       'general_budget_id': 2,
                                       'date_from': date_from, 
                                       'date_to':date_to,
                                       'planned_amount': -vals.subtotal,
                                       }
                self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
                self.pool.get('pnl.order').write(cr,uid,obj.pnl.id,{'budget_id':budget_id})
                self.pool.get('project.project').write(cr,uid,obj.project_id.id,{'budget_id':budget_id})
        
            
            self.write(cr,uid,obj.id,{'state':'change'})
            self.pool.get('project.project').write(cr,uid,obj.pnl.id,{'pnl':obj.pnl.id})
        return True
class pnl_order(osv.osv):
    _inherit='pnl.order'
    
    _columns={
              'request_id':fields.many2one('change.request','CHange')
              }
    def create(self, cr, uid, vals, context=None):
        res={}
        pnl=res=super(pnl_order, self).create(cr, uid, vals, context=context)
        request_id=self.browse(cr,uid,pnl).request_id
        if request_id:
            self.pool.get('change.request').write(cr,uid,request_id.id,{'pnl':pnl})
        return res