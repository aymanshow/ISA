import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields,osv
from openerp.tools.translate import _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil.relativedelta import relativedelta
import pytz
from openerp import netsvc

class hr_department(osv.osv):
    _inherit = "hr.department"
    
    _columns = {
                'sequence_id': fields.many2one('ir.sequence', 'Sequence',),
                'product_ids': fields.many2many('product.product', 'hr_department_product','dept_id','product_id','Products'),
               
                }
    



class job_order(osv.osv):
      _name = "job.order"
      
      def _get_location_id(self, cr, uid, *args):
          user_obj = self.pool.get('res.users').browse(cr,uid,uid)
          if user_obj.location_id:
             return user_obj.location_id.id
          return False
      
      def get_default_department_id(self, cr, uid, context=None):
        """ Gives default department by checking if present in the context """
        user_obj = self.pool.get('res.users').browse(cr,uid,uid).employee_ids 
        if user_obj: 
            dept_id = self.pool.get('res.users').browse(cr,uid,uid).employee_ids[0].department_id and self.pool.get('res.users').browse(cr,uid,uid).employee_ids[0].department_id.id or False
        
        return dept_id
      
      _columns = {
              'name' : fields.char('Name', size=64,required =True),
              'date_order': fields.date('Date',  readonly= True,states={'draft': [('readonly', False)]} ), 
              'user_id': fields.many2one('res.users', 'Request User', ),
              'product_id': fields.many2one('product.product', 'Product',  ),
              'production_lot_id': fields.many2one('stock.production.lot', 'Serial Number', ),
              'location_id': fields.many2one('stock.location', 'Request Location',required =True,readonly= True, states={'draft': [('readonly', False)]},domain=[('usage', '=', 'internal')]),
              'job_order_ref_no' : fields.char('Job Order Reference No',),  
              'state': fields.selection([
                        ('draft', 'Draft'),
                        ('confirm','Confirm'),
                        ('cancel', 'Cancelled'),
                        ('progress', 'In Progress'),
                        ('done', 'Done'),
                        ],'State'),
             'job_line': fields.one2many('job.order.line', 'job_order_id', 'Job Order Lines',),   
             'request_id' : fields.many2one('request.product', 'Request Product',readonly=True), 
             'notes': fields.text('Notes'),  
             'completion_notes': fields.text('Remark'),     
             'vehicle_no' : fields.char('Vehicle number'), 
             'employee_id': fields.many2one('hr.employee','Employee'),   
             'department_id': fields.many2one('hr.department','Department'),       
                 }
      
      _defaults = {
        'date_order': fields.date.context_today,
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'name': lambda obj, cr, uid, context: '/',
        'department_id': lambda self, cr, uid, context: self.get_default_department_id(cr, uid, context),
        'location_id' : _get_location_id,
              #  'employee_id' : _get_employee_id,
               }
     
      def create(self, cr, uid, vals, context=None):
         print "t",self.pool.get('hr.department').browse(cr,uid,self.get_default_department_id(cr, uid, context)).product_ids
         #seq_id = self.pool.get('hr.department').browse(cr,uid,vals['department_id']).sequence_id
         seq_id = self.pool.get('hr.department').browse(cr,uid,self.get_default_department_id(cr, uid, context)).sequence_id
         if seq_id:
             vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, uid, seq_id.id)
         else:    
              vals['name'] = self.pool.get('ir.sequence').next_by_code(cr, uid, 'job.order')
        
         return super(job_order, self).create(cr, uid, vals, context=context)
     
     
     
      def job_open(self, cr, uid, ids, context=None):
        context = context or {}
        
        for o in self.browse(cr, uid, ids):
           
            self.write(cr, uid, [o.id], {'state': 'confirm' })
            
        return True
      
      def job_done(self, cr, uid, ids, context=None):
        context = context or {}
        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'state': 'done' })  
        return True
        
    
        #Merge two or more request and create a new request 
      def request_product(self, cr, uid, ids, context=None):
            """
            
            """
            for request in self.browse(cr, uid, ids, context=context):  
           
           
                pr_dict =   {  
                           'date_order' : request.date_order,
                           'state' : 'draft',
                           'location_id' : request.location_id.id,
                           'request_line' : {},
                           'job_order_id': request.id,
                           'department_id': request.department_id.id,
                           }
            
                pr_id = self.pool.get('request.product').create(cr, uid, pr_dict) 
                for job_line in request.job_line: 
                    job_line = {
                                'product_id' : job_line.product_id.id,
                                'request_product_qty' : job_line.product_qty,
                                'approved_qty' : job_line.product_qty,
                                'request_id' : pr_id,
                                'location_id' : request.location_id.id,
                                } 
                    pr_line_id = self.pool.get('request.product.line').create(cr, uid, job_line)  
            
            self.write(cr,uid,ids,{'state': 'progress','request_id':pr_id})
                                 
            return True
    
class job_order_line(osv.osv):
    _name = "job.order.line"      
      
    _columns = {
                'product_id' : fields.many2one('product.product', 'Product',required =True),
                'desc': fields.char('Description',size=256),
                'product_qty' : fields.integer('Product Qty',required =True),
                'job_order_id' : fields.many2one('job.order', 'Job Order'),
                
                }    
    
    _defaults = {
         'product_qty':1,
       } 
      
      
