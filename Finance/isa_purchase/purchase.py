import time
import re
from openerp.osv import fields, osv
import datetime
from openerp import tools
from openerp.tools.translate import _
import email
import logging
import pytz
import re
import xmlrpclib
from email.message import Message
from openerp.addons.mail.mail_message import decode

from datetime import timedelta
from dateutil import relativedelta
import calendar
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta as td

from datetime import date

from openerp import SUPERUSER_ID
from openerp.addons.mail.mail_message import decode
from openerp.osv import fields, osv, orm
from openerp.tools.safe_eval import safe_eval as eval
import openerp.addons.decimal_precision as dp
import time
import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from openerp import netsvc

class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        #super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
        context = context or {}
        if context.get('default_model') == 'stock.picking.in' and context.get('default_res_id'):
            context = dict(context, mail_post_autofollow=True)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'purchase.order', context['default_res_id'], 'send_rfq', cr)
        return True
        
                
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
              'approve':fields.boolean('Approved',),
              'user_id':fields.many2one('res.users','Approver'),
              'clearing_agent_id':fields.many2one('res.partner','Clearing Agent'),
              }
    _defaults={
               'approve':False
                }
    def write(self,cr,uid,ids,vals,context=None):
        #obj=self.browse(cr,uid,ids)
        if vals.get('awb_no'):
            template_obj = self.pool.get('email.template')
            salesorder_tpl = template_obj.search(cr,uid,[('model_id.model', '=','purchase.order'),('model_object_field.name', '=','awb_no')])
            if salesorder_tpl:                                  
                    mail_id = template_obj.send_mail(cr, uid, salesorder_tpl[0], ids[0], force_send=True, context=context)
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
    


class account_invoice(osv.osv):
    _inherit='account.invoice'
    _columns={
              'state': fields.selection([
            ('draft','Draft'),
            
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            #('payment','Payment Request'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange',),
              
              }
    
    def payment_confirm(self,cr,uid,ids,context):
        self.write(cr,uid,ids,{'state':'paid'})
        return True
        


class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"
    _columns={
              'awb_attachment1':fields.binary('AWB Receipt',),
              'du_attachment1':fields.binary('DU Receipt',),
              'approve':fields.boolean('Approved',readonly=True),
              'user_id':fields.many2one('res.users','Approver'),
              'comments':fields.text('Comments and Review'),
              'state1':fields.selection([('draft','New'),('pending','Pending'),('approve','Approved')],'Status')
              }   
class account_voucher(osv.osv):
    _inherit='account.voucher'
    _columns={
              'invoice_id':fields.many2one('account.invoice'),
              'state':fields.selection(
            [('draft','Draft'),
             ('cancel','Cancelled'),
             ('proforma','Pro-forma'),
             ('payment','Waiting For Payment'),
             ('posted','Posted')
            ], 'Status', readonly=True, size=32, track_visibility='onchange'),
              
            'journal_id':fields.many2one('account.journal', 'Journal', readonly=False, states={'posted':[('readonly',True)]}),
              }
    
    def button_proforma_voucher(self, cr, uid, ids, context=None):
        context = context or {}
        print context
        #self.pool.get('account.invoice').write(cr,uid,context['invoice_id'],{'state':'payment'})
        wf_service = netsvc.LocalService("workflow")
        for vid in ids:
            wf_service.trg_validate(uid, 'account.voucher', vid, 'proforma_voucher', cr)
        return {'type': 'ir.actions.act_window_close'}
    def make_request(self,cr,uid,ids,context=None):
        print "context=======================",context 
        
        self.write(cr,uid,ids,{'state':'payment','invoice_id':context['invoice_id']})
        return True
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            print "move id=======================",move_id
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
            print "ml_writeoff============================",ml_writeoff
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True
    
class stock_picking_in(osv.osv):
    _name = "stock.picking.in"
    _inherit = "stock.picking.in"
    _description = "Incoming Shipments"
    _columns={
              'awb_attachment1':fields.binary('AWB Receipt',),
              'du_attachment1':fields.binary('DU Receipt',),
              'approve':fields.boolean('Approved',readonly=True),
              'user_id':fields.many2one('res.users','Approver'),
              'comments':fields.text('Comments and Review'),
              'state1':fields.selection([('draft','New'),('pending','Pending'),('approve','Approved')],'Status')
              }      
    _defaults={
               'state1':'draft'
               }
    def approve_request(self,cr,uid,ids,context):
        obj=self.browse(cr,uid,ids[0])
        self.write(cr,uid,ids,{'state1':'approve','approve':True})
        self.pool.get('purchase.order').write(cr,uid,obj.purchase_id.id,{'approve':True,'awb_attachment':obj.awb_attachment1,'du_attachment':obj.du_attachment1})
        return True
    def send_mail(self, cr, uid, ids, context=None):
        
            lst=[]
            x = self.browse(cr, uid, ids[0], context=None)
            upload_attachment = x.awb_attachment1
            du_attachment = x.du_attachment1
            approver_name = x.user_id.id
            if upload_attachment and approver_name:
                ir_model_data = self.pool.get('ir.model.data')
                email_template_obj = self.pool.get('email.template')
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','stock.picking.in')], context=context)
                try:
                    template_id = ir_model_data.get_object_reference(cr, uid, 'isa_purchase', 'email_template_edi_purchase')[1]
                except ValueError:
                    template_id = False
                try:
                    compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
                except ValueError:
                    compose_form_id = False
                    
                create_att_id = self.pool.get('ir.attachment').create(cr, uid, {'name':'AWB Receipt', 'type':'binary','res_model':'stock.picking.in','res_id':x.id,'store_fname':'AWB Receipt', 'db_datas':upload_attachment})
                lst.append(create_att_id)
                create_att_id1 = self.pool.get('ir.attachment').create(cr, uid, {'name':'DU Document', 'type':'binary','res_model':'stock.picking.in','res_id':x.id,'store_fname':'AWB Receipt', 'db_datas':du_attachment})
                lst.append(create_att_id1)
                email_template_obj = self.pool.get('email.template')
                                                         
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','stock.picking.in')], context=context)
                
                email_att_id = self.pool.get('email.template').write(cr, uid, template_ids,{'attachment_ids':[[6,0,lst]]})
                ctx = dict(context)
                ctx['default_template_id'] = template_ids[0]
                ctx.update({
                    'default_model': 'stock.picking.in',
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
   
    
        
    

class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('default_model') == 'stock.picking.in' and context.get('default_res_id'):
            context = dict(context, mail_post_autofollow=True)
            self.pool.get('stock.picking.in').write(cr,uid,[context['default_res_id']],{'state1':'pending'})
        if context.get('default_model') == 'purchase.order' and context.get('default_res_id') and context.get('mark_so_as_sent'):
            print'======sendingmail------------------------kafmklamfkamfklafs'
            context = dict(context, mail_post_autofollow=True)
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context) 
    
class stock_partial_picking(osv.osv_memory):
    _inherit = 'stock.partial.picking'
    _columns={
              'comments':fields.text('Comment'),
              
              
              }
    def do_partial(self, cr, uid, ids, context=None):
        obj=self.browse(cr,uid,ids[0])
        self.pool.get('stock.picking.in').write(cr,uid,context['active_id'],{'comments':obj.comments})
        super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        return True
        
class mail_thread(osv.osv):
    _name = "mail.thread"
    _description = "Mails"
    _inherit = "mail.thread"
        
    _columns={
                
            }
    
    def message_parse(self, cr, uid, message, save_original=False, context=None):
        msg_dict = {
                    'type': 'email',
                    'author_id': False,
                }
        if not isinstance(message, Message):
           if isinstance(message, unicode):
                             
              message = message.encode('utf-8')
           message = email.message_from_string(message)
             
        message_id = message['message-id']
        if not message_id:
                         
           message_id = "<%s@localhost>" % time.time()
           import logging
           # _logger.debug('Parsing Message without message-id, generating a random one: %s', message_id)
        msg_dict['message_id'] = message_id
             
        if message.get('Subject'):
           msg_dict['subject'] = decode(message.get('Subject'))
             
                     
        msg_dict['from'] = decode(message.get('from'))
        msg_dict['to'] = decode(message.get('to'))
        msg_dict['cc'] = decode(message.get('cc'))
             
        if message.get('From'):
           author_ids = self._message_find_partners(cr, uid, message, ['From'], context=context)
           if author_ids:
              msg_dict['author_id'] = author_ids[0]
           msg_dict['email_from'] = decode(message.get('from'))
        partner_ids = self._message_find_partners(cr, uid, message, ['To', 'Cc'], context=context)
        msg_dict['partner_ids'] = [(4, partner_id) for partner_id in partner_ids]
             
        if message.get('Date'):
           try:
              date_hdr = decode(message.get('Date'))
              parsed_date = dateutil.parser.parse(date_hdr, fuzzy=True)
              if parsed_date.utcoffset() is None:
                                 
                 stored_date = parsed_date.replace(tzinfo=pytz.utc)
              else:
                 stored_date = parsed_date.astimezone(tz=pytz.utc)
           except Exception:
                 import logging
                 #_logger.warning('Failed to parse Date header %r in incoming mail '
                 #                       'with message-id %r, assuming current date/time.',
                 #                       message.get('Date'), message_id)
                 stored_date = datetime.datetime.now()
           msg_dict['date'] = stored_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
             
        if message.get('In-Reply-To'):
           parent_ids = self.pool.get('mail.message').search(cr, uid, [('message_id', '=', decode(message['In-Reply-To']))])
           if parent_ids:
              msg_dict['parent_id'] = parent_ids[0]
             
        if message.get('References') and 'parent_id' not in msg_dict:
           parent_ids = self.pool.get('mail.message').search(cr, uid, [('message_id', 'in',
                                                                                 [x.strip() for x in decode(message['References']).split()])])
           if parent_ids:
              msg_dict['parent_id'] = parent_ids[0]
        a=[]
        print msg_dict['subject'], "----------------------------------THIS IS SUBJECT OF THE MAIL-------------------------------------"
        string=msg_dict['subject']
        a=string.split(' ')
        res={}
        i=0
        awp=''
        po=''
        po_id=''
        for i in range(len(a)):
            if "AWB" in a[i] :
                awp=a[i]
            if "PO" in a[i]:
                po=a[i]
            po_id=self.pool.get('purchase.order').search(cr,uid,[('name','=',po)])
            print'========po_id======',po_id
            pur_id=self.pool.get('purchase.order').browse(cr,uid,po_id)
            vals=self.pool.get('purchase.order').write(cr, uid,po_id,{'awb_no':awp})  
        
#         for t in self.pool.get('purchase.order').browse(cr,uid,po_id):
#              purchase_id = t.id
             
        msg_dict['body'], msg_dict['attachments'] = self._message_extract_payload(cr, uid, message, save_original=save_original)
#         template_obj = self.pool.get('email.template')
#         salesorder_tpl = template_obj.search(cr,uid,[('model_id.model', '=','purchase.order'),('model_object_field.name', '=','awb_no')])
#         print'=======sTEMPLATE=====',salesorder_tpl
#         if salesorder_tpl:                                  
#                mail_id = template_obj.send_mail(cr, uid, salesorder_tpl[0], purchase_id, force_send=True, context=context)
#                print'------mail_id=====',mail_id
        return msg_dict
       
    def _message_extract_payload(self, cr, uid, message, save_original=False):
        """Extract body as HTML and attachments from the mail message"""
             
        print "tttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt"
             
        attachments = []
        body = u''
             
        if save_original:
                 
            attachments.append(('original_email.eml', message.as_string()))
        if not message.is_multipart() or 'text/' in message.get('content-type', ''):
            encoding = message.get_content_charset()
            body = message.get_payload(decode=True)
            body = tools.ustr(body, encoding, errors='replace')
            if message.get_content_type() == 'text/plain':
                     
                body = tools.append_content_to_html(u'', body, preserve=True)
        else:
                 
                 
            alternative = (message.get_content_type() == 'multipart/alternative')
            for part in message.walk():
                     
                if part.get_content_maintype() == 'multipart':
                    continue  
                filename = part.get_filename()  
                     
                encoding = part.get_content_charset()  
                     
                if filename or part.get('content-disposition', '').strip().startswith('attachment'):
                         
                    attachments.append((filename or 'attachment', part.get_payload(decode=True)))
                         
                    #self.import_attendance(cr,uid,part.get_payload())
                         
                    continue
                     
                if part.get_content_type() == 'text/plain' and (not alternative or not body):
                    body = tools.append_content_to_html(body, tools.ustr(part.get_payload(decode=True),
                                                                         encoding, errors='replace'), preserve=True)
                     
                elif part.get_content_type() == 'text/html':
                    html = tools.ustr(part.get_payload(decode=True), encoding, errors='replace')
                    if alternative:
                        body = html
                    else:
                        body = tools.append_content_to_html(body, html, plaintext=False)
                     
                else:
                         
                         
                    attachments.append((filename or 'attachment', part.get_payload(decode=True)))
             
        print body, "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu"
        return body, attachments
   
   
   
   
mail_thread()

        