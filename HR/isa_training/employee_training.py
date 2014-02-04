from osv import osv
from osv import fields
import time
from datetime import datetime
from openerp import tools
from openerp.tools.translate import _
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
TRAVEL_MODE=[
             ('flight','Flight'),
             ('train','Train'),
             ('bus','Bus'),
             ]
class employee_training1(osv.osv):
    _name='employee.training1'
    _rec_name='training_state'
    def create(self, cr, uid, vals, context=None):
        if not vals:
            vals = {}
        if context is None:
            context = {}
        vals['traing_id'] = self.pool.get('ir.sequence').get(cr, uid, 'employee.training1')
        return super(employee_training1, self).create(cr, uid, vals, context=context)
    _columns={
              'traing_id':fields.char('Training Id',readonly=True),
              'emp_id':fields.char('Employee Id'),
              'emp_name_id':fields.many2one('hr.employee','Employee Name'),
              'department_id':fields.many2one('hr.department','Department'),
              'date_from':fields.date('Date From'),
              'date_to':fields.date('Date To'),
              'location':fields.char('Training Location'),
              'cost_of_certificate':fields.float('Cost of Certificate'),

              'description':fields.text('Certificate Description'),
              'training_state': fields.selection(AVAILABLE_STATES, 'States',help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
              'manager_comment':fields.text("Manager's Comments"),
              'travel_mode_line':fields.one2many('travel.mode','travel_mide_id','Travel Information',required=True),
              'hotel_management_line':fields.one2many('hotel.management','hotel_management_id','Hotel Information',required=True),
               'visa_approval_line':fields.one2many('visa.approval','visa_approval_id','Hotel Information',required=True),
               'awating_approwal_line':fields.one2many('awating.certificate','awating_approval_id','Awaiting Approval'),
               'certificat_approv_line':fields.one2many('certificate.information','certificate_inform_id','Certificate Information'),
              }
    _order = 'traing_id desc'
    _defaults = {
                 'training_state':'draft',
                 'traing_id': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'employee.training1'),
                 }
    
    def onchange_employee_id(self,cr,uid,ids,emp_name_id,context=None):
             res={}
             info=''
             hr_employee_obj=self.pool.get('hr.employee')
             line= hr_employee_obj.browse(cr,uid,emp_name_id)
             vals=line.department_id.id
             if vals == False:
                raise osv.except_osv(('Warning!'),('This Employee is not assigned the department please assign the Department'))
             else:
                 res ={
                       'department_id':line.department_id.id,
                       'emp_id':line.identification_id,
                       } 
                 return {'value': res}
             
             
    def action_submit(self,cr,uid,ids,context=None):
        list=[]
        certi_obj=self.pool.get('certificate.information'),
        awating_cert_obj=self.pool.get('awating.certificate')
        obj=self.browse(cr,uid,ids[0])
        if not obj.certificat_approv_line:
            raise osv.except_osv(('Warning !'),('Please enter the certificate information.'))
        else:
           for app in obj.certificat_approv_line:
                     list.append((0,0,{'certificate_name':app.name}))
        self.write(cr,uid,ids,{'awating_approwal_line':list})
        self.write(cr, uid, ids, {'training_state': 'approval'})
        return {'value': {'awating_approwal_line': list}}
 
    def action_certfied(self,cr,uid,ids,context=None):
        awating_obj=self.pool.get('awating.certificate')
        obj=self.browse(cr,uid,ids[0])
        if obj.awating_approwal_line:
            for val in obj.awating_approwal_line:
                if not val.is_certified:
                    raise osv.except_osv(('Warning!'),('Please select the Result'))     
                if val.is_certified =='p':
                    self.write(cr, uid, ids, {'training_state': 'done'})
                if val.is_certified =='f':
                     raise osv.except_osv(('Warning!'),('Employee has not cleared "%s" so you can not move the training form to certified state\n\n Please click on "Pending" till Pass certificate is submitted by employee')% (val.certificate_name))    
        return True
    
    def action_pending(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'training_state': 'pending'})
        return True
    def action_approve(self,cr,uid,ids,context=None):
         obj=self.browse(cr,uid,ids[0])
         if obj.training_state=='approval':
                    self.write(cr, uid, ids,{'training_state':'legal_process'})
         if obj.training_state=='legal_process':
                      self.write(cr, uid, ids,{'training_state':'payment'})
         if obj.training_state=='payment':
                   self.write(cr, uid, ids,{'training_state':'awaiting_certificate'})
         if obj.training_state=='awaiting_certificate':
                   self.write(cr, uid, ids,{'training_state':'pending'})
         if obj.training_state=='pending':
                   self.write(cr, uid, ids,{'training_state':'done'})
         if obj.training_state=='done':
                   self.write(cr, uid, ids,{'training_state':'done'})
         return True
    def action_cancel(self, cr, uid, ids, context=None):
        """Overrides cancel for crm_case for setting probability
        """
        self.write(cr, uid, ids, {'training_state':'refuse'})
        return True
    def action_complete(self,cr,uid,ids,context=None):
        acc_invoice_obj=self.pool.get('account.invoice')
        obj=self.browse(cr,uid,ids[0])
        travel_obj=self.pool.get('travel.mode')
        hotel_obj=self.pool.get('hotel.management')
        visa_obj=self.pool.get('visa.approval')
        if not obj.certificat_approv_line:
            pass
        else:
           for app in obj.certificat_approv_line:
                  certified_id=acc_invoice_obj.search(cr,uid,[('number','=',app.invoice_id.number),('state','=','open')])
                  if not certified_id:
                      raise osv.except_osv(('Warning !'),('Please create and validate certificate invoice.'))
                  else:
                      self.write(cr, uid, ids, {'training_state':'payment'})    
        if not obj.travel_mode_line:
            pass
        else:
           for val in obj.travel_mode_line:
                  travel_id=acc_invoice_obj.search(cr,uid,[('number','=',val.invoice_id.number),('state','=','open')])
                  if not travel_id:
                      raise osv.except_osv(('Warning!'),('Please create and validate Travel invoice.'))
                  else:
                      self.write(cr, uid, ids, {'training_state':'payment'})            
        if not obj.hotel_management_line:
           pass
        else:
            for res in obj.hotel_management_line:
                hotel_id=acc_invoice_obj.search(cr,uid,[('number','=',res.invoice_id.number),('state','=','open')])
                if not hotel_id:
                      raise osv.except_osv(('Warning!'),('Please create and validate  Hotel Invoice.'))
                else:
                    self.write(cr, uid, ids, {'training_state':'payment'})       
        if not obj.visa_approval_line:
           pass
        else:
            for chk in obj.visa_approval_line:
                visa_id=acc_invoice_obj.search(cr,uid,[('number','=',chk.invoice_id.number),('state','=','open')])
                if not visa_id:
                      raise osv.except_osv(('Warning!'),('Please create and validate visa Invoice.'))
                else:
                      self.write(cr, uid, ids, {'training_state':'payment'})       
        return True
    def action_pending_certfied(self,cr,uid,ids,context=None):
            awating_obj=self.pool.get('awating.certificate')
            obj=self.browse(cr,uid,ids[0])
            if obj.awating_approwal_line:
                flag=0
                for val in obj.awating_approwal_line:
                    if val.is_certified =='p':
                        flag=1
                    else:
                        flag=0
                if flag==1:
                    self.write(cr, uid, ids, {'training_state': 'done'}) 
                else:
                     raise osv.except_osv(('Warning!'),('Please attached the certificate and result field set is pass'))           
                return True
       
    def action_paid(self,cr,uid,ids,context=None):
        acc_invoice_obj=self.pool.get('account.invoice')
        obj=self.browse(cr,uid,ids[0])
        travel_obj=self.pool.get('travel.mode')
        hotel_obj=self.pool.get('hotel.management')
        visa_obj=self.pool.get('visa.approval')
        if not obj.certificat_approv_line:
            pass
        else:
           for app in obj.certificat_approv_line:
                   certified_id=acc_invoice_obj.search(cr,uid,[('number','=',app.invoice_id.number),('state','=','paid')])
                   if not certified_id:
                      raise osv.except_osv(('Warning!'),('Please pay the certificate invoice before proceeding'))
                   else:
                        self.write(cr, uid, ids, {'training_state':'awaiting_certificate'}) 
        if not obj.travel_mode_line:
            pass
        else:
           for val in obj.travel_mode_line:
                  travel_id=acc_invoice_obj.search(cr,uid,[('number','=',val.invoice_id.number),('state','=','paid')])
                  if not travel_id:
                      raise osv.except_osv(('Warning!'),('Please pay the travel invoice before proceeding'))
                  else:
                    self.write(cr, uid, ids, {'training_state':'awaiting_certificate'})            
        if not obj.hotel_management_line:
           pass
        else:
            for res in obj.hotel_management_line:
                hotel_id=acc_invoice_obj.search(cr,uid,[('number','=',res.invoice_id.number),('state','=','paid')])
                if not hotel_id:
                      raise osv.except_osv(('Warning!'),('Please pay the hotel invoice before proceeding'))
                else:
                    self.write(cr, uid, ids, {'training_state':'awaiting_certificate'}) 
            
        if not obj.visa_approval_line:
           pass
        else:
            for chk in obj.visa_approval_line:
                visa_id=acc_invoice_obj.search(cr,uid,[('number','=',chk.invoice_id.number),('state','=','paid')])
                if not visa_id:
                      raise osv.except_osv(('Warning!'),('Please pay the visa invoice before proceeding'))
                else:
                    self.write(cr, uid, ids, {'training_state':'awaiting_certificate'}) 
        
        return True
class travel_mode(osv.osv):
    _name='travel.mode'
    
    def action_crete_invoice(self,cr,uid,ids,context=None):
         curr_user=self.pool.get('res.users').search(cr, uid, [('id','=',uid)])
         for cu in self.pool.get('res.users').browse(cr,uid,curr_user):
            curr_company = self.pool.get('res.company').search(cr, uid, [('id','=',cu.company_id.id)])
            curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors - (test)')])
            if curr_account==[]:
                curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors')])
            for ac in self.pool.get('account.account').browse(cr, uid, curr_account):
                account_id = ac.id
         if ids:
            obj=self.browse(cr,uid,ids[0])
            inv=self.pool.get('account.invoice').onchange_company_id(cr, uid, ids, cu.company_id.id, obj.agency_name_id.id, 'in_invoice', [(0,0,{'quantity':1,'price_unit':obj.ticket_cost,'name':obj.travel_mode,'account_id':account_id})],obj.agency_name_id.company_id.currency_id.id,)
            journal_id=inv['value']['journal_id']
            invoice_id=obj.invoice_id and obj.invoice_id.id or False
            if not invoice_id:
                invoice_id=self.pool.get('account.invoice').create(cr,uid,{     
                                                                                  'journal_id':journal_id,
                                                                                  'type':'in_invoice',
                                                                                  'partner_id':obj.agency_name_id.id,
                                                                                  'account_id':account_id,
                                                                                  'company_id':cu.company_id.id,
                                                                                  'reference_type':'none',
                                                                                  'currency_id':obj.agency_name_id.company_id.currency_id.id,
                                                                                  'invoice_line':[(0,0,{'invoice_id':invoice_id,'quantity':1,'price_unit':obj.ticket_cost,'name':obj.travel_mode})],
                                                                                  })
                self.write(cr,uid,obj.id,{'invoice_id':invoice_id})
                
         return {
                 'name':'Invoice',
                'res_model':'account.invoice',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'form,tree',
                'target':'current',
                'res_id':invoice_id,
                'nodestroy': True,
                'target': 'new',
                'context':context.update({'active_model':'account.invoice','active_ids':[invoice_id],'active_id':invoice_id}),
                'domain':[('id','in',[invoice_id])]
                }
         
         
    def invoice_pay_customer1(self, cr, uid, ids, context=None):
            travel_obj=self.pool.get('travel.mode')
            invoice_obj=self.pool.get('account.invoice')
            obj=self.browse(cr,uid,ids[0])
            travel_id=invoice_obj.search(cr, uid, [('id','=',obj.invoice_id.id),('state','=','open')])
            if not travel_id:
                raise osv.except_osv(('Warning!'),('This Invoice is already paid'))
            if not travel_id: return []
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
            inv = invoice_obj.browse(cr, uid, travel_id[0], context=context)
            return {
                'name':_("Pay Invoice"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': {
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                }
            }
            
    _columns={
              'travel_mode':fields.selection(TRAVEL_MODE, 'Travel Mode',help="Select The Traveling mode"),
              'trave_date':fields.date('Travel Date'),
              'agency_name_id':fields.many2one('res.partner','Agency Name'),
              'ticket_cost':fields.float('Cost Of Ticket'),
              'journey_type':fields.selection([('up','UP'),('down','DOWN')],'Journey Type'),
              'source':fields.char('Source'),
              'destination':fields.char('Destination'),
              'attach':fields.binary('Attach Ticket'),
              'invoice_id':fields.many2one('account.invoice','Invoice Number',readonly=True),
              'invoice_number': fields.related('account.invoice','number',type='selection', string='Product Type', selection=[('X','X'),('Y','Y'),('Z','Z')]),
              'travel_mide_id':fields.many2one('employee.training1','travel relation'),
               'training_state_id': fields.related('travel_mide_id','training_state',type="selection",selection=[('draft', 'New'),
                                                    ('approval', 'Approval'),
                                                    ('legal_process', 'Legal Process'),
                                                    ('payment', 'Payment'),
                                                    ('awaiting_certificate', 'Awaiting Certificate'),
                                                    ('pending', 'Pending'),
                                                    ('done', 'Certified'),
                                                    ('refuse', 'Rejected')] ,help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),

              }
class hotel_management(osv.osv):
    _name='hotel.management'
    
    def action_crete_invoice(self,cr,uid,ids,context=None):
         curr_user=self.pool.get('res.users').search(cr, uid, [('id','=',uid)])
         for cu in self.pool.get('res.users').browse(cr,uid,curr_user):
            curr_company = self.pool.get('res.company').search(cr, uid, [('id','=',cu.company_id.id)])
            curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors - (test)')])
            if curr_account==[]:
                curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors')])
            for ac in self.pool.get('account.account').browse(cr, uid, curr_account):
                account_id = ac.id
         if ids:
            obj=self.browse(cr,uid,ids[0])
            inv=self.pool.get('account.invoice').onchange_company_id(cr, uid, ids, cu.company_id.id, obj.hotel_name_id.id, 'in_invoice', [(0,0,{'quantity':1,'price_unit':obj.hotel_cost,'name':obj.hotel_address})],obj.hotel_name_id.company_id.currency_id.id,)
            journal_id=inv['value']['journal_id']
            invoice_id=obj.invoice_id and obj.invoice_id.id or False
            if not invoice_id:
                invoice_id=self.pool.get('account.invoice').create(cr,uid,{     
                                                                                  'journal_id':journal_id,
                                                                                  'type':'in_invoice',
                                                                                  'partner_id':obj.hotel_name_id.id,
                                                                                  'account_id':account_id,
                                                                                  'company_id':cu.company_id.id,
                                                                                  'reference_type':'none',
                                                                                  'currency_id':obj.hotel_name_id.company_id.currency_id.id,
                                                                                  'invoice_line':[(0,0,{'invoice_id':invoice_id,'quantity':1,'price_unit':obj.hotel_cost,'name':obj.hotel_address})],
                                                                                  })
                self.write(cr,uid,obj.id,{'invoice_id':invoice_id})
                
         return {
                 'name':'Invoice',
                'res_model':'account.invoice',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'form,tree',
                'target':'current',
                'res_id':invoice_id,
                'nodestroy': True,
                'target': 'new',
                'context':context.update({'active_model':'account.invoice','active_ids':[invoice_id],'active_id':invoice_id}),
                'domain':[('id','in',[invoice_id])]
                }
    def invoice_pay_customer1(self, cr, uid, ids, context=None):
            hotel_obj=self.pool.get('hotel.management')
            invoice_obj=self.pool.get('account.invoice')
            obj=self.browse(cr,uid,ids[0])
            hotel_id=invoice_obj.search(cr, uid, [('id','=',obj.invoice_id.id),('state','=','open')])
            if not hotel_id:
                raise osv.except_osv(('Warning!'),('This Invoice is already paid'))
            if not hotel_id: return []
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
            inv = invoice_obj.browse(cr, uid, hotel_id[0], context=context)
            return {
                'name':_("Pay Invoice"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': {
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                }
            }
    def onchange_hotel_name_id(self,cr,uid,ids,hotel_name_id,context=None):
             res={}
             info=''
             hr_employee_obj=self.pool.get('res.partner')
             line= hr_employee_obj.browse(cr,uid,hotel_name_id)
             phone=line.phone
             if not phone:
                      raise osv.except_osv(('Warning!'),('Configure the Supplier and enter the phone number'))              
             mob=line.mobile
             if not mob:
                      raise osv.except_osv(('Warning!'),('Configure the Supplier and enter the mobile number'))    
             vals=line.street
             vals1=line.street2
             vals2=line.city
             vals3=line.state_id.name 
             vals4=line.country_id.name
             addrs=str(vals)+' '+str(vals1)+' '+str(vals2)+' '+str(vals3)+' '+str(vals4)
             if addrs == False:
                        raise osv.except_osv(('Warning!'),('This Employee is not assigned the department please assign the Department'))
             else:
                         res ={
                               'hotel_address':addrs,
                               'phone_num':phone,
                               'contact_num':mob
                               } 
             return {'value': res}
    _columns={
              'hotel_name_id':fields.many2one('res.partner','Hotel Name'),
              'hotel_address':fields.char('Hotel Address'),
              'contact_num':fields.char('Contact Number'),
              'phone_num':fields.char('Phone Number'),
              'hotel_cost':fields.float('Cost'),
              'attachment':fields.binary('Attachment'),
              'invoice_id':fields.many2one('account.invoice','Invoice Number',readonly=True),
              'hotel_management_id':fields.many2one('employee.training1','Hotel relation','Hotel Management'),
               'training_state_id': fields.related('hotel_management_id','training_state',type="selection",selection=[('draft', 'New'),
                                                    ('approval', 'Approval'),
                                                    ('legal_process', 'Legal Process'),
                                                    ('payment', 'Payment'),
                                                    ('awaiting_certificate', 'Awaiting Certificate'),
                                                    ('pending', 'Pending'),
                                                    ('done', 'Certified'),
                                                    ('refuse', 'Rejected')] ,help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),

              }
class visa_approval(osv.osv):
    _name='visa.approval'
    
    def action_crete_invoice(self,cr,uid,ids,context=None):
         curr_user=self.pool.get('res.users').search(cr, uid, [('id','=',uid)])
         for cu in self.pool.get('res.users').browse(cr,uid,curr_user):
            curr_company = self.pool.get('res.company').search(cr, uid, [('id','=',cu.company_id.id)])
            curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors - (test)')])
            if curr_account==[]:
                curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors')])
            for ac in self.pool.get('account.account').browse(cr, uid, curr_account):
                account_id = ac.id
         if ids:
            obj=self.browse(cr,uid,ids[0])
            inv=self.pool.get('account.invoice').onchange_company_id(cr, uid, ids, cu.company_id.id, obj.visa_company_id.id, 'in_invoice', [(0,0,{'quantity':1,'price_unit':obj.visa_cost,'name':obj.country})],obj.visa_company_id.company_id.currency_id.id,)
            journal_id=inv['value']['journal_id']
            invoice_id=obj.invoice_id and obj.invoice_id.id or False
            if not invoice_id:
                invoice_id=self.pool.get('account.invoice').create(cr,uid,{     
                                                                                  'journal_id':journal_id,
                                                                                  'type':'in_invoice',
                                                                                  'partner_id':obj.visa_company_id.id,
                                                                                  'account_id':account_id,
                                                                                  'company_id':cu.company_id.id,
                                                                                  'reference_type':'none',
                                                                                  'currency_id':obj.visa_company_id.company_id.currency_id.id,
                                                                                  'invoice_line':[(0,0,{'invoice_id':invoice_id,'quantity':1,'price_unit':obj.visa_cost,'name':obj.country})],
                                                                                  })
                self.write(cr,uid,obj.id,{'invoice_id':invoice_id}) 
            return {
                 'name':'Invoice',
                'res_model':'account.invoice',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'form,tree',
                'target':'current',
                'res_id':invoice_id,
                'nodestroy': True,
                'target': 'new',
                'context':context.update({'active_model':'account.invoice','active_ids':[invoice_id],'active_id':invoice_id}),
                'domain':[('id','in',[invoice_id])]
                }
    
    
    def invoice_pay_customer1(self, cr, uid, ids, context=None):
            visa_obj=self.pool.get('visa.approval')
            invoice_obj=self.pool.get('account.invoice')
            obj=self.browse(cr,uid,ids[0])
            visa_id=invoice_obj.search(cr, uid, [('id','=',obj.invoice_id.id),('state','=','open')])
            if not visa_id:
                raise osv.except_osv(('Warning!'),('This Invoice is already paid'))
            if not visa_id: return []
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
    
            inv = invoice_obj.browse(cr, uid, visa_id[0], context=context)
            return {
                'name':_("Pay Invoice"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': {
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                }
            }
    _columns={
              'visa_company_id':fields.many2one('res.partner','Visa Company'),
              'visa_id':fields.char('Visa Id'),
              'country':fields.char('Country'),
              'valid_from':fields.date('Valid From'),
              'valid_to':fields.date('Valid To'),
              'visa_cost':fields.float('Visa Cost'),
               'invoice_id':fields.many2one('account.invoice','Invoice Number',readonly=True),
              'visa_approval_id':fields.many2one('employee.training1','visa relation'),
               'training_state_id': fields.related('visa_approval_id','training_state',type="selection",selection=[('draft', 'New'),
                                                    ('approval', 'Approval'),
                                                    ('legal_process', 'Legal Process'),
                                                    ('payment', 'Payment'),
                                                    ('awaiting_certificate', 'Awaiting Certificate'),
                                                    ('pending', 'Pending'),
                                                    ('done', 'Certified'),
                                                    ('refuse', 'Rejected')] ,help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
              }
class awating_certificate(osv.osv):
    _name='awating.certificate'
    _columns={
              'certificate_name':fields.char('Certificate Name',readonly=True),
              'grade':fields.char('Grade'),
              'clear_date':fields.date('Date'),
              'attach':fields.binary('Attachment'),
              'is_certified':fields.selection([('p','Pass'),('f','Fail')],'Result'),
             'certi_rel':fields.many2one('certificate.information','Certificate Relation'),
             'awating_approval_id':fields.many2one('employee.training1','Awating relation'),
             'training_state_id': fields.related('awating_approval_id','training_state',type="selection",selection=[('draft', 'New'),
                                                    ('approval', 'Approval'),
                                                    ('legal_process', 'Legal Process'),
                                                    ('payment', 'Payment'),
                                                    ('awaiting_certificate', 'Awaiting Certificate'),
                                                    ('pending', 'Pending'),
                                                    ('done', 'Certified'),
                                                    ('refuse', 'Rejected')] ,help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),

              }

awating_certificate()

class certificate_information(osv.osv):
    _name='certificate.information'
    
    def action_crete_invoice(self,cr,uid,ids,context=None):
         curr_user=self.pool.get('res.users').search(cr, uid, [('id','=',uid)])
         for cu in self.pool.get('res.users').browse(cr,uid,curr_user):
            curr_company = self.pool.get('res.company').search(cr, uid, [('id','=',cu.company_id.id)])
            curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors - (test)')])
            if curr_account==[]:
                curr_account = self.pool.get('account.account').search(cr, uid, [('company_id','=',cu.company_id.id),('name','=','Creditors')])
            for ac in self.pool.get('account.account').browse(cr, uid, curr_account):
                account_id = ac.id
         if ids:
            obj=self.browse(cr,uid,ids[0])
            inv=self.pool.get('account.invoice').onchange_company_id(cr, uid, ids, cu.company_id.id, obj.certificate_vendor_id.id, 'in_invoice', [(0,0,{'quantity':1,'price_unit':obj.cost,'name':obj.name})], obj.certificate_vendor_id.company_id.currency_id.id)
            journal_id=inv['value']['journal_id']
            invoice_id=obj.invoice_id and obj.invoice_id.id or False
            if not invoice_id:
                invoice_id=self.pool.get('account.invoice').create(cr,uid,{
                                                                                 'journal_id':journal_id,
                                                                                  'type':'in_invoice',
                                                                                  'partner_id':obj.certificate_vendor_id.id,
                                                                                  'supplier':1,
                                                                                  'account_id':account_id,
                                                                                  'company_id':cu.company_id.id,
                                                                                  'reference_type':'none',
                                                                                  'currency_id':obj.certificate_vendor_id.company_id.currency_id.id,
                                                                                  'invoice_line':[(0,0,{'invoice_id':invoice_id,'quantity':1,'price_unit':obj.cost,'name':obj.name})]
                                                                                  })
                self.write(cr,uid,obj.id,{'invoice_id':invoice_id})
                
         return {
                 'name':'Invoice',
                'res_model':'account.invoice',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'form,tree',
                'target':'current',
                'res_id':invoice_id,
                'nodestroy': True,
                'target': 'new',
                'context':context.update({'active_model':'account.invoice','active_ids':[invoice_id],'active_id':invoice_id}),
                'domain':[('id','in',[invoice_id])]
                }
         
    def invoice_pay_customer1(self, cr, uid, ids, context=None):
            certificate_obj=self.pool.get('certificate.information')
            invoice_obj=self.pool.get('account.invoice')
            obj=self.browse(cr,uid,ids[0])
            
            certificate_id=invoice_obj.search(cr, uid, [('id','=',obj.invoice_id.id),('state','=','open')])
            
            if not certificate_id:
                raise osv.except_osv(('Warning!'),('This Invoice is already paid'))
            if not certificate_id: return []
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
            inv = invoice_obj.browse(cr, uid, certificate_id[0], context=context)
            return {
                'name':_("Pay Invoice"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': {
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                }
            }
    _columns={
              'name':fields.char('Certificate Name'),
              'cost':fields.float('Certificate Cost'),
              'training_state_id': fields.related('certificate_inform_id','training_state',type="selection",selection=[('draft', 'New'),
                                                    ('approval', 'Approval'),
                                                    ('legal_process', 'Legal Process'),
                                                    ('payment', 'Payment'),
                                                    ('awaiting_certificate', 'Awaiting Certificate'),
                                                    ('pending', 'Pending'),
                                                    ('done', 'Certified'),
                                                    ('refuse', 'Rejected')] ,help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed."),
              'certificate_vendor_id':fields.many2one('res.partner','Vendor'),
              'invoice_id':fields.many2one('account.invoice','Invoice Number',readonly=True),
              'certi_rel':fields.many2one('awating.certificate','Certificate Relation'),
              'certificate_inform_id':fields.many2one('employee.training1','Certificate Relation'),
              }
certificate_information()





