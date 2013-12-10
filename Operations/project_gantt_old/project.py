from osv import osv
from osv import fields
import openerp.addons.decimal_precision as dp
import time
from openerp.tools.translate import _

class mail_compose_message(osv.TransientModel):
    _inherit='mail.compose.message'
    
    def send_mail(self, cr, uid, ids, context=None):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """
        for z in self.browse(cr, uid, ids, context=None):
            main_form_id = z.res_id
        print main_form_id, "ttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt"
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
                print search_project_form, "-----------------------------------------------------------"
                
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
                
                #self.write(cr, uid, ids, {'state_for_sr': 'sent_for_approval'})
        return {'type': 'ir.actions.act_window_close'}

    
    
    
    
class project_project(osv.osv):
    _inherit='project.project'
    
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
              'solution_review':fields.binary('Solution Review Comments'),
              'project':fields.binary('Project Charter'),
              'finance_document':fields.binary('Finance Documents'),
              'solution':fields.binary('Solution Review'),
              'training_plan':fields.binary('Training Plan'),
              'technical_plan':fields.binary('Technical Plan'),
              'implementation_plan':fields.binary('Master Implementation Plan'),
              'state': fields.selection([('template', 'Template'),
                        ('draft','New'),('initiate','Initiate'),
                        ('plan','Planning'),('execute','Execution'),('open','In Progress'),
                         ('cancelled', 'Cancelled'),('pending','Pending'),
                         ('close','Closed')], 'Status', required=True,),
              'filename1': fields.char('File Name',size=256),
              'filename2': fields.char('File Name',size=256),
              'filename3': fields.char('File Name',size=256),
              'filename4': fields.char('File Name',size=256),
              
              'sr_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              'ko_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              'pc_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              'fd_approve_id':fields.many2one('hr.employee','Select Approver',domain="[('department_name', 'in', ('Executive Director','Operations Director'))]"),
              
              
              
              'sr_id':fields.many2one('res.users','Select Approver'),
              'ko_id':fields.many2one('res.users','Select Approver'),
              'pc_id':fields.many2one('res.users','Select Approver'),
              'fd_id':fields.many2one('res.users','Select Approver'),
              
              
              #'sr_upload': fields.function(_data_get_kick, fnct_inv=_data_set_kick, string='Upload File', type="binary", nodrop=True),
              #'ko_upload': fields.function(_data_get_kick, fnct_inv=_data_set_kick, string='Upload Presentation', type="binary", nodrop=True),
              #'pc_upload': fields.function(_data_get_kick, fnct_inv=_data_set_kick, string='Upload File', type="binary", nodrop=True),
              #'fd_upload': fields.function(_data_get_kick, fnct_inv=_data_set_kick, string='Upload File', type="binary", nodrop=True),
              
              'sr_upload': fields.binary('Upload File1'),
              'ko_upload': fields.binary('Upload File2'),
              'pc_upload': fields.binary('Upload File3'),
              'fd_upload': fields.binary('Upload File4'),
              
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
    
    def onchange_sr_approve_id(self, cr, uid, ids, sr_approve_id):
            v={}
            if sr_approve_id:
               partner1=self.pool.get('hr.employee').browse(cr, uid, sr_approve_id)
               v['sr_id']=partner1.user_id.id
               #v['department_id']=partner1.id
            print "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
            print v
            return {'value':v}
        
    def onchange_ko_approve_id(self, cr, uid, ids, ko_approve_id):
            v={}
            if ko_approve_id:
               partner2=self.pool.get('hr.employee').browse(cr, uid, ko_approve_id)
               v['ko_id']=partner2.user_id.id
               #v['department_id']=partner1.id
            print "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
            print v
            return {'value':v}
        
    def onchange_pc_approve_id(self, cr, uid, ids, pc_approve_id):
            v={}
            if pc_approve_id:
               partner3=self.pool.get('hr.employee').browse(cr, uid, pc_approve_id)
               v['pc_id']=partner3.user_id.id
               #v['department_id']=partner1.id
            print "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
            print v
            return {'value':v}
        
    def onchange_fd_approve_id(self, cr, uid, ids, fd_approve_id):
            v={}
            if fd_approve_id:
               partner4=self.pool.get('hr.employee').browse(cr, uid, fd_approve_id)
               v['fd_id']=partner4.user_id.id
               #v['department_id']=partner1.id
            print "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
            print v
            return {'value':v}
    
    def start_project(self,cr,uid,ids,context):
        self.write(cr,uid,ids[0],{'state':'initiate'})
        
        return True
    def planning(self,cr,uid,ids,context):
        self.write(cr,uid,ids[0],{'state':'plan'})
        return True
    def execute(self,cr,uid,ids,context):
        self.write(cr,uid,ids[0],{'state':'execute'})
        return True
    
    
    
    
    
    def send_mail_sr(self, cr, uid, ids, context=None):
        print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        print ids, "'''''''''''''''''''''''''' THE MAIN FORM ID''''''''''''''''''''''''''''''''''''''''"
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.sr_upload
            approver_name = x.sr_id.id
            print upload_attachment, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            print create_att_id, "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn" 
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            
            print email_att_id, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
             
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
        print "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        print ids, "'''''''''''''''''''''''''' THE MAIN FORM ID''''''''''''''''''''''''''''''''''''''''"
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.ko_upload
            approver_name = x.ko_id.id
            print upload_attachment, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            print create_att_id, "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn" 
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            
            print email_att_id, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
             
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
        print "ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
        print "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        print ids, "'''''''''''''''''''''''''' THE MAIN FORM ID''''''''''''''''''''''''''''''''''''''''"
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.pc_upload
            approver_name = x.pc_id.id
            print upload_attachment, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            print create_att_id, "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn" 
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            
            print email_att_id, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
             
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
        print "ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
        print "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        print ids, "'''''''''''''''''''''''''' THE MAIN FORM ID''''''''''''''''''''''''''''''''''''''''"
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.fd_upload
            approver_name = x.fd_id.id
            print upload_attachment, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'Attachment', 'type':'binary', 'datas':upload_attachment})
            print create_att_id, "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn" 
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            
            print email_att_id, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
             
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
        print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        self.write(cr, uid, ids, {'state_for_sr': 'approved'})
        return True
    
    def approve_by_admin_ko(self,cr,uid,ids,context=None):
        print "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        self.write(cr, uid, ids, {'state_for_ko': 'approved'})
        return True
    
    def approve_by_admin_pc(self,cr,uid,ids,context=None):
        print "gggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg"
        self.write(cr, uid, ids, {'state_for_pc': 'approved'})
        return True
    
    def approve_by_admin_fd(self,cr,uid,ids,context=None):
        print "hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"
        self.write(cr, uid, ids, {'state_for_fd': 'approved'})
        return True
    
    def send_mail_approve(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        print ids, "'''''''''''''''''''''''''' THE MAIN FORM ID''''''''''''''''''''''''''''''''''''''''"
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.sr_upload
            approver_name = x.sr_id.id
            print upload_attachment, "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'project_gantt', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'My Attachment', 'type':'binary', 'datas':upload_attachment})
            print create_att_id, "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
            print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn" 
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,[create_att_id]]]})
            
            print email_att_id, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
             
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
            
    
    
#     def send_mail_approve(self, cr, uid, ids, context=None):
#             test=[]
#             email_template_obj = self.pool.get('email.template')
#             ir_model_data = self.pool.get('ir.model.data')
#             template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
#             if template_ids:
#                 values = email_template_obj.generate_email(cr, uid, template_ids[0], ids, context=context)
#                 email_obj=self.browse(cr,uid,ids[0])
#                 try:
#                     compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
#                 except ValueError:
#                     compose_form_id = False
#                 
# #                if not email_obj.approve_id.id:
# #                    raise osv.except_osv(
# #                                _('Error!'),
# #                                _('Please fill the applicant '))
#                 values['res_id'] = False
#                 mail_mail_obj = self.pool.get('mail.mail')
#                 msg_id = mail_mail_obj.create(cr, uid, values, context=context)
#                 if msg_id:
#                     mail_mail_obj.send(cr, uid, [msg_id], context=context)
#                 ctx = dict(context)
# #                user_partner_ids=self.pool.get('res.partner').search(cr,uid,[('email','=',email_obj.approve_id.email)])
#                 ctx['default_template_id'] = template_ids[0]
# #                ctx['default_receiver_email'] = email_obj.approve_id.email
# #                ctx['default_partner_ids'] = user_partner_ids
#                 return {
#                         'type': 'ir.actions.act_window',
#                         'view_type': 'form',
#                         'view_mode': 'form',
#                         'res_model': 'mail.compose.message',
#                         'views': [(compose_form_id, 'form')],
#                         'view_id': compose_form_id,
#                         'target': 'new',
#                         'context': ctx,
#                         }

#
    
#    def send_mail_approve(self,cr,uid, ids,context=None):
#        for certi_obj1 in self.browse(cr,uid, ids,context=None):
#            if not certi_obj1.datas and not certi_obj1.approve_id.id:
#                    raise osv.except_osv(
#                        _('Error!'),
#                        _('You cannot send mail until select Approver and Upload Presentation'))
#            elif not certi_obj1.approve_id.id:
#                raise osv.except_osv(
#                    _('Error!'),
#                    _('You cannot send mail until select Approver'))
#            elif not certi_obj1.datas:
#                raise osv.except_osv(
#                    _('Error!'),
#                    _('You cannot send mail until select Upload Presentation'))
#            if certi_obj1.approve_id.id and certi_obj1.datas:
#                test_email=self.pool.get('res.users').browse(cr,uid,certi_obj1.approve_id.id).email
#                mail_mail = self.pool.get('mail.mail')
#                asunto = 'Kick-off Validation'
#                body = '' 
#                body += '<br/>'
#                body = 'Hello sir' 
#                body += '<br/>' 
#                body += 'Need to approve your validation' 
#                body += '<br/>' 
#                body += 'Thank you'
#                mail_ids = []
#                mail_ids.append(mail_mail.create(cr, uid, {
#                                'email_from': "dhawalsharma786@gmail.com",
#                                'email_to': test_email,
#                                'subject': asunto,
#                                'body_html': '<pre>%s</pre>' % body}, context=context))
#                mail_mail.send(cr, uid, mail_ids, context=context)
#            self.write(cr, uid, ids, {'state_for_appr': 'sent_for_approval'})
#        return True
    
    def approve_by_admin(self,cr,uid,ids,context=None):
        if not ids:
            ids=self.search(cr,uid,ids)
        for certi_obj in self.browse(cr,uid, ids,context=None):
            if not certi_obj.datas and not certi_obj.approve_id.id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You cannot send mail until select Approver and Upload Presentation'))
            elif not certi_obj.approve_id.id:
                raise osv.except_osv(
                    _('Error!'),
                    _('You cannot send mail until select Approver'))
            elif not certi_obj.datas:
                raise osv.except_osv(
                    _('Error!'),
                    _('You cannot send mail until select Upload Presentation'))
            if certi_obj.approve_id.id and certi_obj.datas:
                #self.write(cr, uid, ids, {'state_for_appr': 'approval'})
                print "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
        return True
        
    def send_mail_approve_doc(self,cr,uid, ids,context=None):
        for certi_obj in self.browse(cr,uid, ids,context=None):
                approver_id = certi_obj.approve_id.id
                print approver_id, "jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj"
#             if not certi_obj.datas_project_charter and not certi_obj.approve_project_charter_id.id :
#                     raise osv.except_osv(
#                         _('Error!'),
#                         _('You cannot send mail until select Approver and Upload Project Document'))
#             elif not certi_obj.datas_project_charter:
#                     raise osv.except_osv(
#                         _('Error!'),
#                         _('You cannot send mail until select Upload Project Document'))
#             elif not certi_obj.approve_project_charter_id.id:
#                     raise osv.except_osv(
#                         _('Error!'),
#                         _('You cannot send mail until select Approver'))
#             if certi_obj.approve_project_charter_id.id and certi_obj.datas_project_charter:
                email_template_obj = self.pool.get('email.template')
                                                 
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','project.project')], context=context)
                print template_ids, "nnnnnnnnnnnnnnnnnnnnn TEMPLATE ID OBTAINED nnnnnnnnnnnnnnnnnnnnnnnnn"
        
                if template_ids:                                  
                    mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], ids[0], force_send=True, context=context)
#                 test_email=self.pool.get('res.users').browse(cr,uid,certi_obj.approve_project_charter_id.id).email
#                 mail_mail = self.pool.get('mail.mail')
#                 asunto = 'Product Document Validation'
#                 body = '' 
#                 body += '<br/>'
#                 body = 'Hello sir' 
#                 body += '<br/>' 
#                 body += 'Need to approve your validation' 
#                 body += '<br/>' 
#                 body += 'Thank you'
#                 mail_ids = []
#                 mail_ids.append(mail_mail.create(cr, uid, {
#                                 'email_from': "drishtitechtestmail@gmail.com",
#                                 'email_to': test_email,
#                                 'subject': asunto,
#                                 'body_html': '<pre>%s</pre>' % body}, context=context))
#                 mail_mail.send(cr, uid, mail_ids, context=context)
                #self.write(cr, uid, ids, {'state_for_appr_project': 'sent_for_approval'})
        return True
    
    def approve_by_pro_admin(self,cr,uid,ids,context=None):
        if not ids:
            ids=self.search(cr,uid,ids)
        for certi_obj in self.browse(cr,uid, ids,context=None):
            if not certi_obj.datas_project_charter and not certi_obj.approve_project_charter_id.id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You cannot send mail until select Approver and Upload Project Document'))
            elif not certi_obj.approve_project_charter_id.id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You cannot send mail until select Approver'))
                
            elif not certi_obj.datas_project_charter:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You cannot send mail until select Upload Project Document'))
                
            if certi_obj.approve_project_charter_id.id and certi_obj.datas_project_charter:
                print "mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm"
                #self.write(cr, uid, ids, {'state_for_appr_project': 'approval'})
        return True

    
class project_task(osv.osv):
    _inherit='project.task'
    _columns={
              'depends_on':fields.many2one('project.task','Depends On'),
              'days_needed':fields.integer('Days Needed To '),
              'state':fields.related('project_id','state', type='selection',selection=[('template', 'Template'),
                        ('draft','New'),('initiate','Initiate'),
                        ('plan','Planning'),('execute','Execution'),('open','In Progress'),
                         ('cancelled', 'Cancelled'),('pending','Pending'),
                         ('close','Closed')], string='State'),
              }