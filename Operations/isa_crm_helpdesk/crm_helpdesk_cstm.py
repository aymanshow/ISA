from osv import fields, osv
import datetime
from datetime import datetime, timedelta
import time
from openerp import tools
from tools.translate import _
from openerp import netsvc
from openerp.addons.crm import crm
import openerp.addons.decimal_precision as dp

AVAILABLE_STATES = [ 
    ('draft', 'New'),
    ('open', 'In Progress'),
    ('awaiting', 'Awaiting Approval'),# add extra stage
    ('pending', 'On Duty'),
    ('cancel', 'Cancelled'),
    ('done', 'Closed'),
]

class job_order_numbers(osv.osv):
    _name = "job.order.numbers"
    _description = "Job Order Numbers"
    _columns = {
                'job_number':fields.many2one('crm.helpdesk','Job Number'),
                'name':fields.many2one('job.order1','Job Order Number', size=64),
                }

class crm_helpdesk(osv.osv):
    _inherit = "crm.helpdesk"
    _description = "Crm Contract Form"
    _rec_name = "ticket_no"
    _columns = {
        'ticket_no':fields.char('Ticket No.',size=64),
        #'form_ticket_no':fields.many2one('job.order1','Job Order Id'),
        'job_order_line':fields.one2many('job.order.numbers','job_number','Job Order Line'),
        'contracts_partner':fields.many2one('res.partner','Customer Name',required=True),
        'contracts':fields.many2one('account.analytic.account','Contracts',required=True),
        'problem_type':fields.many2one('problem.type','Problem Type',required=True),
        'categ_id1': fields.many2one('crm.case.categ', 'Problem Category',required=True),
        'engineer_id':fields.many2one('res.users','Engineer',required=True),
        'user_id1': fields.many2one('res.users', 'Supervisor', required=True),
        'supervisor_name': fields.many2one('res.users', 'Supervisor Name'),
        'state': fields.selection(AVAILABLE_STATES, 'Status', size=16, readonly=True,
                                  help='The status is set to \'Draft\', when a case is created.\
                                  \nIf the case is in progress the status is set to \'Open\'.\
                                  \nWhen the case is over, the status is set to \'Done\'.\
                                  \nIf the case needs to be reviewed then the status is set to \'On Duty\'.'),
        'approved_by':fields.many2one('res.users','Approver'),
        'customer_visit':fields.char('Customer during visit',size=256),
        'remark':fields.text('Customer Remarks'),
        }
    
    
    _defaults = {
        'active': lambda *a: 1,
        'approved_by': lambda obj, cr, uid, context: uid,
        'partner_id': lambda s, cr, uid, c: s._get_default_partner(cr, uid, c),
        'email_from': lambda s, cr, uid, c: s._get_default_email(cr, uid, c),
        'state': lambda *a: 'draft',
        'date': lambda *a: fields.datetime.now(),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'crm.helpdesk', context=c),
        'priority': lambda *a: crm.AVAILABLE_PRIORITIES[2][0],
        'ticket_no': lambda obj, cr, uid, context: '/',
    }
    
    def print_report(self,cr,uid,ids,context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'crm.helpdesk', ids[0], 'new', cr)
        datas = {
                 'model': 'crm.helpdesk',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'engineer_ticket', 'datas': datas, 'nodestroy': True}
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('ticket_no','/')=='/':
            vals['ticket_no'] = self.pool.get('ir.sequence').get(cr, uid,'crm.helpdesk') or '/'
        return super(crm_helpdesk, self).create(cr, uid, vals, context=context)
 
    def case_open1(self, cr, uid, ids, context=None):
        for res in self.browse(cr, uid,ids):
            if not res.user_id1.id and not res.engineer_id.id:
                raise osv.except_osv(
                            _('Error!'),
                            _('Please select the Supervisor & Assign engineer before going ahead'))
                
            elif not res.user_id1.id:
                raise osv.except_osv(
                            _('Error!'),
                            _('Please select the Supervisor'))
                
                
            if not res.contracts_partner.id and not res.contracts.id:
                raise osv.except_osv(
                            _('Error!'),
                            _('Please select the Customer Name & Contracts before going ahead'))
           
            
            elif not res.contracts_partner.id:
                raise osv.except_osv(
                            _('Error!'),
                            _('Please select the Customer Name'))
                
            elif not res.contracts.id:
                raise osv.except_osv(
                            _('Error!'),
                            _('Please select the Contracts'))
                
            elif not res.engineer_id.id:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please Assign engineer before going ahead'))
                
                
                
        if not isinstance(ids,list): ids = [ids]
        return self.case_set(cr, uid, ids, 'open', {'date_start': fields.datetime.now()}, context=context)
    
    
    def create_job_order(self, cr, uid, ids, context=None):
            contract_obj=self.browse(cr,uid,ids[0])
            obj=self.browse(cr,uid,ids[0]).contracts_partner
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'isa_crm_helpdesk', 'job_order_form1')
            
            return {
                'name':_("Job Order"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'job.order1',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': {
                   'default_customer_name':obj.id,
                   'default_phone':obj.phone,
                   'default_mobile':obj.mobile,
                   'default_email':obj.email,
                   'default_contract_id':contract_obj.contracts.id,
                   'default_ticket_form_id':contract_obj.ticket_no,
                   'default_street':obj.street,
                   'default_street2':obj.street2,
                   'default_zip':obj.zip,
                   'default_city':obj.city,
                   'default_state_id':obj.state_id.id,
                   'default_country_id':obj.country_id.id,
                   'default_engineer_id':contract_obj.engineer_id.id,
                }
            }
            
    def action_approve(self,cr,uid,ids,context=None):
        crm_obj=self.browse(cr,uid,ids[0])
        job_id=self.pool.get('job.order1').search(cr,uid,[('ticket_form_id','=',crm_obj.ticket_no)])
        if job_id:
            self.pool.get('job.order1').write(cr,uid,job_id[0],{'supervisor_name': crm_obj.approved_by.id})
        self.write(cr, uid, ids, {'state': 'pending'})
        return True        
            
    def onchange_partner(self,cr,uid,ids,contract,context=None):
        res={}
        if contract:
            obj=self.pool.get('account.analytic.account').browse(cr, uid, contract)
            res['value']= {'contracts_partner':obj.partner_id.id}
        else:
            res['domain'] = {'contracts_partner': []}
        return res
        
    def onchange_categ_id(self, cr, uid, ids, categ_id1, context=None):
        if categ_id1:
            record_obj=self.pool.get('crm.case.categ').browse(cr,uid,categ_id1)
            member_ids = record_obj.section_id.member_ids
            domain_value = []
            if member_ids:
                domain_value = [('id','in',[x.id for x in member_ids])]
            else:
                domain_value = []
            return {'domain':{'engineer_id':domain_value}}
                
     
    def onchange_contracts_partner(self, cr, uid, ids, contracts_partner, email=False, context=None):
        res={}
        list=[]
        if contracts_partner:
            person_record_ids=self.pool.get('account.analytic.account').search(cr,uid,[('partner_id','=',contracts_partner)])
            address = self.pool.get('res.partner').browse(cr, uid, contracts_partner)
            if not address.email:
                    mail=False
            else:
                mail=address.email
            res['domain'] = {'contracts': [('id', 'in', person_record_ids)]}
            res['value']={'email_from':mail}
        else:
            res['domain'] = {'contracts': []}
            res['value'] = {'email_from':False}
        return res
    
class problem_type(osv.osv):
    _name = 'problem.type'
    _order = "id desc"
    _columns ={
               'name':fields.char('Problem',size=256)
               }

class job_order1(osv.osv):
    _name='job.order1'
    def _data_get(self, cr, uid, ids, name, arg, context=None):
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

    def _data_set(self, cr, uid, id, name, value, arg, context=None):
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
            super(job_order1, self).write(cr, uid, [id], {'store_fname': fname, 'file_size': file_size}, context=context)
        else:
            super(job_order1, self).write(cr, uid, [id], {'db_datas': value, 'file_size': file_size}, context=context)
        return True
        
    _columns={
               'name':fields.char('Job Order Id'),
               #'ticket_form_id':fields.char('Ticket Form Id'),
               'ticket_form_id':fields.many2one('crm.helpdesk','Ticket Form Id'),
               'customer_name':fields.many2one('res.partner','Customer Name'),
               'address': fields.char('Address'),
               'phone':fields.char('Phone Number',size=64),
               'mobile':fields.char('Mobile',size=64),
               'email':fields.char('Email',size=64),
               'contract_id':fields.many2one('account.analytic.account','Contracts'),
               'visit_date_time':  fields.datetime('Date & Time'),
               'tool_require_ids':fields.one2many('required.products','product_line_id','Tools Required'),
               'street': fields.char('Street', size=128),
               'street2': fields.char('Street2', size=128),
               'zip': fields.char('Zip', change_default=True, size=24),
               'city': fields.char('City', size=128),
               'state_id': fields.many2one("res.country.state", 'State'),
               'country_id': fields.many2one('res.country', 'Country'),
               'country': fields.related('country_id', type='many2one', relation='res.country', string='Country',
                                  deprecated="This field will be removed as of OpenERP 7.1, use country_id instead"),
               'engineer_id':fields.many2one('res.users','Engineer'),
               
               'supervisor_name': fields.many2one('res.users', 'Supervisor'),
               'customer': fields.char('Customer Name',size=64),
               'person_at_time_of_visit': fields.char('Person at the time of Visit',size=64),
                                            
               'job_state': fields.selection([('draft','Draft'),
                                              ('new','New'),
                                              ('completed', 'Completed')],'Status',readonly=True,),
               'remark':fields.text('Visit Remarks'),
#               Take field for binary attach file
               
               'datas': fields.function(_data_get, fnct_inv=_data_set, string='Attachment', type="binary", nodrop=True),
               'store_fname': fields.char('Stored Filename', size=256),
               'db_datas': fields.binary('Database Data'),
               'file_size': fields.integer('File Size'),
               'datas_fname': fields.char('File Name',size=256),
              }
    
    
    _order = 'name desc'
    _defaults={
               'name': lambda obj, cr, uid, context: '/',
               'job_state':'draft'
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid,'job.order1') or '/'
        return super(job_order1, self).create(cr, uid, vals, context=context)
    
    def action_save(self, cr, uid, vals, context=None):
        return True
    
    def action_submit(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        for x in self.browse(cr,uid,ids,context=None):
            ticket_form_id = x.ticket_form_id.id
            
        if context.get('active_id'):
            self.pool.get('crm.helpdesk').write(cr,uid,int(context.get('active_id')),{'state': 'awaiting','form_ticket_no':obj.id})
            self.pool.get('job.order.numbers').create(cr,uid, {'name':ids[0], 'job_number':ticket_form_id})
        self.write(cr, uid, ids, {'job_state': 'new'})
        return True
    
    def action_completed(self,cr,uid,ids,context=None):
        job_obj=self.browse(cr,uid,ids[0])
        ticket_no=job_obj.ticket_form_id
        crm_id=self.pool.get('crm.helpdesk').search(cr,uid,[('ticket_no','=',ticket_no)])
        if crm_id:
            self.pool.get('crm.helpdesk').write(cr,uid,crm_id[0],{'customer_visit':job_obj.customer,'remark':job_obj.remark})
        self.write(cr, uid, ids, {'job_state': 'completed'})
        return True
    
    def action_print(self,cr,uid,ids,context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'job.order1', ids[0], 'new', cr)
        datas = {
                 'model': 'job.order1',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'engineer_job_order', 'datas': datas, 'nodestroy': True}
       # return True



class required_products(osv.osv):
    _name='required.products'
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'serial_num' : fields.function(get_serial_no,type='integer',string='Sr.No'),
              'product_line_id':fields.many2one('job.order1','Tools',invisible=True),
              'product':fields.many2one('product.product','Required Products'),
              'product_qty':fields.integer('Quantity'),
              'remarks':fields.text('Remarks'),
              
              }
