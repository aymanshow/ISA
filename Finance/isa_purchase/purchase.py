from osv import osv
from osv import fields
import openerp.addons.decimal_precision as dp
import time
import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
import purchase



class mail_compose_message(osv.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
        context = context or {}
        if context.get('default_model') == 'purchase.order' and context.get('default_res_id'):
            context = dict(context, mail_post_autofollow=True)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'purchase.order', context['default_res_id'], 'send_rfq', cr)
        return 
        
                
                #self.write(cr, uid, ids, {'state_for_sr': 'sent_for_approval'})
       

class purchase_order(osv.osv):
    _inherit='purchase.order'
    _name='purchase.order'
    STATE_SELECTION = [
                        ('draft', 'Draft PO'),
                        ('sent', 'RFQ Sent'),
                        ('confirmed', 'Waiting Approval'),
                        ('approved', 'Purchase Order'),
                        ('except_picking', 'Shipping Exception'),
                        ('except_invoice', 'Invoice Exception'),
                        ('done', 'Done'),
                        ('cancel', 'Cancelled')
                      ]
    _columns={
              'awb_no':fields.char('AWB No.',size=32),
              'state': fields.selection(STATE_SELECTION, 'Status', readonly=True, help="The status of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' status. Then the order has to be confirmed by the user, the status switch to 'Confirmed'. Then the supplier must confirm the order to change the status to 'Approved'. When the purchase order is paid and received, the status becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the status becomes in exception.", select=True),
              'awb_attachment':fields.binary('AWB Receipt'),
              'du_attachment':fields.binary('DU Receipt'),
              'approve':fields.boolean('Approved',readonly=True),
              'user_id':fields.many2one('res.users','Approver'),
              }
    _defaults={
               'approve':False
               
               }
    def send_mail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        lst=[]
        for x in self.browse(cr, uid, ids, context=None):
            upload_attachment = x.awb_attachment
            du_attachment = x.du_attachment
            approver_name = x.user_id.id
        if upload_attachment and approver_name:
            ir_model_data = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','purchase.order')], context=context)
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'isa_purchase', 'email_template_edi_purchase')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
                
            create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'AWB Receipt', 'type':'binary', 'datas':upload_attachment})
            lst.append(create_att_id)
            create_att_id1 = self.pool.get('ir.attachment').create(cr, uid, {'name':'DU Document', 'type':'binary', 'datas':du_attachment})
            lst.append(create_att_id1)
            email_template_obj = self.pool.get('email.template')
                                                     
            template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','purchase.order')], context=context)
            
            email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,lst]]})
            
            ctx = dict(context)
            ctx['default_template_id'] = template_ids[0]
            ctx.update({
                'default_model': 'purchase.order',
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
    
    def view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        mod_obj = self.pool.get('ir.model.data')
        wizard_obj = self.pool.get('purchase.order.line_invoice')
        #compute the number of invoices to display
        obj=self.browse(cr,uid,ids[0])
        if obj.approve == False:
            raise osv.except_osv(_('Warning!'),_('Can not Create invoice until the document get approved'))
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            if po.invoice_method == 'manual':
                if not po.invoice_ids:
                    context.update({'active_ids' :  [line.id for line in po.order_line]})
                    wizard_obj.makeInvoices(cr, uid, [], context=context)

        for po in self.browse(cr, uid, ids, context=context):
            inv_ids+= [invoice.id for invoice in po.invoice_ids]
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        res_id = res and res[1] or False

        return {
            'name': _('Supplier Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'in_invoice', 'journal_type': 'purchase'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }

        
        
        
