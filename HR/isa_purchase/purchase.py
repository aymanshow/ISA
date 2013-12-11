from osv import osv
from osv import fields
import openerp.addons.decimal_precision as dp
import time
import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
import purchase
from openerp import netsvc


class mail_compose_message(osv.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
        context = context or {}
        if context.get('default_model') == 'stock.picking.in' and context.get('default_res_id'):
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
              'approve':fields.boolean('Approved',),
              'user_id':fields.many2one('res.users','Approver'),
              }
    _defaults={
               'approve':False
               
               }

    
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
        print "context=========================================",context
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
        
        