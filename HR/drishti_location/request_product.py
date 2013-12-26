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

#======================================================================================
## Add request_id field in stock picking to add the request.product id value 
#======================================================================================
class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _columns = {
                 'request_id' : fields.many2one('request.product', 'Request Product'),
                 'workshop_id': fields.many2one('stock.location', 'Product Location'),
                }

#     def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#             print "context",context
#             user_obj = self.pool.get('res.users').browse(cr, uid, uid,context)
#            # if user_obj.location_ids:
#                 #ids = self.pool.get('request.product').search(cr, uid,  [])
#                # print "test"
#             return super(stock_picking, self).search(cr, uid,  args, offset=0, limit=None, order=None, context=context)

##======================================================================
# Create request.product class for product request
##======================================================================

class request_product(osv.osv):
      _name = "request.product"
      
      
      def get_default_department_id(self, cr, uid, context=None):
        """ Gives default department by checking if present in the context """
        user_obj = self.pool.get('res.users').browse(cr,uid,uid).employee_ids 
        if user_obj: 
            dept_id = self.pool.get('res.users').browse(cr,uid,uid).employee_ids[0].department_id and self.pool.get('res.users').browse(cr,uid,uid).employee_ids[0].department_id.id or False
        
        return dept_id
      
      # get location related to user
      def _get_location_id(self, cr, uid, *args):
          user_obj = self.pool.get('res.users').browse(cr,uid,uid)
          if user_obj.location_id:
             return user_obj.location_id.id
          return False
      
      # get employee id related to user
      def get_employee_id(self, cr, uid, *args):
          
          employee_id =  self.pool.get('hr.employee').search(cr,uid,[('user_id','=',uid)]) and self.pool.get('hr.employee').search(cr,uid,[('user_id','=',uid)])[0] or False
          
          return employee_id
      
      # if all the product related to request are deliver then request_product converted into done state
      
#       def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#           user_obj = self.pool.get('res.users').browse(cr, uid, uid, context)
#           print "user_obj.location_ids",user_obj.location_ids
#           if user_obj.location_ids:
#                ids = super(request_product, self).search(cr, uid, [('location_id', 'in', [l.id for l in user_obj.location_ids])] +args, offset=0, limit=None, order=None, context=context)
#           else:
#                print "here"
#                ids = super(request_product, self).search(cr, uid,  args, offset=0, limit=None, order=None, context=context)    
#           for request in self.browse(cr, uid, ids, context=context):
#               print "request",request
#               flag =True
#               for picking in request.picking_ids:
#                   print "picking", picking.state
#                   if picking.state != 'done':
#                      flag = False
#               if flag and request.state == 'progress':
#                   self.write(cr, uid, request.id, {'state' : 'done'})
#              
#           return ids
            
      
      def check_picking(self,cr,uid,ids, name, arg, context=None):
        res = {}
         
        for request in self.browse(cr, uid, ids, context=context):
          flag =True
          
          for picking in request.picking_ids:
              
              if picking.state != 'done':
                 flag = False
          if flag and request.state == 'progress':
              self.write(cr, uid, request.id, {'state' : 'done'})
              for line in request.request_line:
                  self.pool.get('request.product.line').write(cr, uid, line.id, {'state' : 'done'})
              res[request.id] = True
        return res
      
      _columns = {
                  'name' : fields.char('Name', size=64),
                  'date_order': fields.date('Date', required=True, readonly=True, states={'draft': [('readonly', False)]}), 
                  'user_id': fields.many2one('res.users', 'Request User', readonly=True, states={'draft': [('readonly', False)]}  ),
                  'location_id': fields.many2one('stock.location', 'Request Location', readonly=True, states={'draft': [('readonly', False)]},domain=[('usage', '=', 'internal')]),
                  'req_ref_no' : fields.char('Request Reference No',readonly=True, states={'draft': [('readonly', False)]}),  
                  #'request_detail_line': fields.one2many('request.product.detail.line', 'request_id', 'Request Detail Lines',),
                  'state': fields.selection([
                        ('draft', 'Draft'),
                        ('sent', 'Request Sent'),
                        ('cancel', 'Cancelled'),
                        ('Approved', 'Approved By Supervisor'),
                        ('progress', 'In Progress'),
                        ('done', 'Done'),
                        ],'State'),
                 'request_line': fields.one2many('request.product.line', 'request_id', 'Request Lines',),   
                 'picking_ids': fields.one2many('stock.picking', 'request_id', 'Related Picking', help="This is a list of move that has been generated for this request."),
                 'picking': fields.function(check_picking, string='Picking', type='boolean'),
                 'employee_id': fields.many2one('hr.employee','Employee'),   
                 'requistion_id': fields.many2one('purchase.requisition','Purchase Requisition'),  
                 'job_order_id' : fields.many2one('job.order', 'Job Order Ref',readonly=True), 
                 'department_id': fields.many2one('hr.department','Department'),          
                 }
      
      _defaults = {
        'date_order': fields.date.context_today,
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'name': lambda obj, cr, uid, context: '/',
        'location_id' : _get_location_id,
        'department_id': lambda self, cr, uid, context: self.get_default_department_id(cr, uid, context),
      #  'employee_id' : _get_employee_id,
       }
      #_sql_constraints = [
       # ('name_uniq', 'unique(name)', 'Order Reference must be unique per Company!'),
      #]
      
      def onchange_user_id(self, cr, uid, ids, user_id, context=None):
        v = {}
        if user_id:
            user = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
            if user.location_id.id:
                v['location_id'] = user.location_id.id
                return {'value': v}
        return {'value' : {}}
    
#       def create(self, cr, uid, vals, context=None):
#     
#                print "vals",vals
#                seq_id = self.pool.get('stock.location').browse(cr,uid,vals['location_id']).sequence_id
#                if seq_id:
#                     vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, uid, seq_id.id)
#                else:
#                     vals['name'] = self.pool.get('ir.sequence').next_by_code(cr, uid, 'request.product')
#                
#                return super(request_product, self).create(cr, uid, vals, context=context)
    
      #Merge two or more request and create a new request 
      def do_merge(self, cr, uid, ids, context=None):
        """
        
        """
        
        for prequest in [request for request in self.browse(cr, uid, ids, context=context) ]:
            if prequest.state != 'sent' :
                 raise osv.except_osv(_('Error!'),_('You cannot merge a Request which is not in confirm state.'))  
                
        #TOFIX: merged order line should be unlink
        new_request = {}
        pr_dict =   {  
                       'date_order' : datetime.today(),
                       'state' : 'draft',
                       'user_id' : uid,
                       'request_detail_line' : {},
                       }
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        if user_obj.location_id:
             pr_dict['location_id'] = user_obj.location_id.id
        print "test",pr_dict
        pr_id = self.pool.get('request.product').create(cr, uid, pr_dict) 
        dic = {}
        dic1 = {}
        for prequest in [request for request in self.browse(cr, uid, ids, context=context) ]:    
            #for request_line in prequest.request_detail_line:
            for request_line in prequest.request_line:    
                pr_line_list = []
                if dic.has_key(request_line.product_id):
                     dic[request_line.product_id]['request_product_qty'] += request_line.approved_qty
                     dic[request_line.product_id]['approved_qty'] += request_line.approved_qty
                     dic1[request_line.product_id].append(request_line.id)
                else:
                    dic[request_line.product_id] = {
                           'product_id' : request_line.product_id.id,
                           'request_product_qty' : request_line.approved_qty,
                           'approved_qty' : request_line.approved_qty,
                           'request_id' : pr_id,
                           }
                    if user_obj.location_id:
                       dic[request_line.product_id]['location_id'] = user_obj.location_id.id
                    dic1[request_line.product_id] = [request_line.id]
        self.action_ship_create(cr, uid, ids, context=context)        
        import pprint 
        pprint.pprint(dic)
        print "dic1",dic1 
        for key in dic1.keys():
            line_id = self.pool.get('request.product.line').create(cr, uid, dic[key])
            for detail_id in dic1[key]:
                #self.pool.get('request.product.detail.line').write(cr, uid, detail_id, {'request_line_id' : line_id})
                self.pool.get('request.product.line').write(cr, uid, detail_id, {'parent_id' : line_id})
                             
        return True
       
      
      def confirm_request(self, cr, uid, ids, context=None):
        context = context or {}
        
        for o in self.browse(cr, uid, ids):
            seq_id = self.pool.get('stock.location').browse(cr,uid,o.location_id.id).sequence_id
            if seq_id:
                    name = self.pool.get('ir.sequence').next_by_id(cr, uid, seq_id.id)
            else:
                    name = self.pool.get('ir.sequence').next_by_code(cr, uid, 'request.product')
            self.pool.get('request.product').write(cr, uid, o.id, {'name': name})        
            if not o.request_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a Request which has no line.'))
            else:
               for line in o.request_line:
                #self.pool.get('request.product.line').write(cr, uid, line.id, {'approved_qty' : line.request_product_qty,'state': 'sent'})
                   self.pool.get('request.product.line').write(cr, uid, line.id, {'state': 'sent'})
            #for detail_line in o.request_detail_line:
             #   self.pool.get('request.product.detail.line').write(cr, uid, detail_line.id, {'approved_qty' : detail_line.request_product_qty})   
               self.write(cr, uid, [o.id], {'state': 'sent', })
            
        return True
    
      def cancel_request(self, cr, uid, ids, context=None):
        context = context or {}
        for o in self.browse(cr, uid, ids):
            
            for line in o.request_line:
                print "test1"
                self.pool.get('request.product.line').write(cr, uid, line.id, {'state' : 'cancel'})
            #for detail_line in o.request_detail_line:
             #   self.pool.get('request.product.detail.line').write(cr, uid, detail_line.id, {'approved_qty' : detail_line.request_product_qty})   
            self.write(cr, uid, [o.id], {'state': 'cancel', })
            
        return True
      
      def date_to_datetime(self, cr, uid, userdate, context=None):
        """ Convert date values expressed in user's timezone to
        server-side UTC timestamp, assuming a default arbitrary
        time of 12:00 AM - because a time is needed.
    
        :param str userdate: date string in in user time zone
        :return: UTC datetime string for server-side use
        """
        # TODO: move to fields.datetime in server after 7.0
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
        if context and context.get('tz'):
            tz_name = context['tz']
        else:
            tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            user_datetime = user_date + relativedelta(hours=12.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


      def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        
        if  user_obj.location_id.id:
             location_id = user_obj.location_id.id
        else:
            location_id = self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Stock')]) \
                          and self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Stock')])[0] or False   
        return {
            'name': line.product_id.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': order.date_order,
            'date_expected': order.date_order,
            'product_qty': line.approved_qty,
            'product_uom': line.product_id.uom_id.id,
            'product_uos_qty': line.approved_qty,
            'product_uos': line.product_id.uom_id.id,
            'location_id': location_id,
            'location_dest_id': line.location_id.id,
            #'sale_line_id': line.id,
            'state': 'draft',
            #'state': 'waiting',
           # 'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0
        }

      
      def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        if user_obj.location_id:
            location_id = user_obj.location_id.id
        else:
             location_id = False
        return {
            'name': pick_name,
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'type': 'internal',
            'state': 'auto',
            'request_id': order.id,
            'location_dest_id':order.location_id.id,
            'location_id': location_id,
            'department_id': order.department_id.id,
        #    'note': order.note,
           # 'company_id': order.company_id.id,
        }
      
      
      def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """
        """
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
           
        for line in order_lines:
            
            if line.state == 'progress':
               print "Progress"    
                #continue

            date_planned = order.date_order

            if line.product_id:
                
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        

        
        return True

      def action_ship_create(self, cr, uid, ids, context=None):
        for d in self.browse(cr, uid, ids, context=None):
            request_user=d.user_id.id
            #user_id=d.employee_id.user_id.id
            
            
            if request_user==uid:
                
                raise osv.except_osv(('Error!!'),('You cannot approve your own request'))  
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
          
        for request in self.browse(cr, uid, ids, context=context):
          
          
          if request.location_id.id <> user_obj.location_id.id:
         # if 1 ==1:    
            for line in request.request_line:
                
                self.pool.get('request.product.line').write(cr, uid, line.id, {'state': 'progress'})
                
            self._create_pickings_and_procurements(cr, uid, request, request.request_line, None, context=context)
            
            self.write(cr, uid, [request.id], {'state': 'progress' }) 
          else:
              raise osv.except_osv(_('Warning!'), _('you are not authorized to approve this request'))     
        return True
    
      def generate_delivery(self, cr, uid, ids, context=None):
        context = context or {}
        return True
          
      def request_in_progress(self, cr, uid, ids, context=None):
        context = context or {}
        
        for o in self.browse(cr, uid, ids):
            for line in o.request_line:
                print "test"
                self.pool.get('request.product.line').write(cr, uid, line.id, {'state': 'progress'})
            #for detail_line in o.request_detail_line:
             #   self.pool.get('request.product.detail.line').write(cr, uid, detail_line.id, {'approved_qty' : detail_line.request_product_qty})   
            self.write(cr, uid, [o.id], {'state': 'progress' })
            
        return True
    
    
    
    #Merge two or more request and create a new request 
      def do_merge1(self, cr, uid, ids, context=None):
        """
        
        """
        
        for prequest in [request for request in self.browse(cr, uid, ids, context=context) ]:
            if prequest.state != 'sent' :
                 raise osv.except_osv(_('Error!'),_('You cannot merge a Request which is not in confirm state.'))  
                
        #TOFIX: merged order line should be unlink
        new_request = {}
        pr_dict =   {  
                       'date_start' : datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                       'state' : 'draft',
                       'user_id' : uid,
                       'line_ids' : {},
                       }
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        
        print "test",pr_dict
        pr_id = self.pool.get('purchase.requisition').create(cr, uid, pr_dict) 
        dic = {}
        dic1 = {}
        for prequest in [request for request in self.browse(cr, uid, ids, context=context) ]:  
            self.write(cr, uid,prequest.id,{'requistion_id':pr_id})  
            #for request_line in prequest.request_detail_line:
            for request_line in prequest.request_line:    
                pr_line_list = []
                if dic.has_key(request_line.product_id):
                     dic[request_line.product_id]['product_qty'] += request_line.approved_qty
                     
                     dic1[request_line.product_id].append(request_line.id)
                else:
                    dic[request_line.product_id] = {
                           'product_id' : request_line.product_id.id,
                           'product_qty' : request_line.approved_qty,
                           'requisition_id' : pr_id,
                           }
                    
                    dic1[request_line.product_id] = [request_line.id]
        
        for key in dic1.keys():
            line_id = self.pool.get('purchase.requisition.line').create(cr, uid, dic[key])
            
                             
        return True
    
class request_product_line(osv.osv):
    _name = "request.product.line" 
    
    def _get_location_id(self, cr, uid, *args):
          print "arg",args 
          user_obj = self.browse(cr,uid,uid)
          if user_obj.location_id:
             return user_obj.location_id.id
          return False      
      
    _columns = {
                'product_id' : fields.many2one('product.product', 'Product',required =True,readonly=True, states={'draft': [('readonly', False)]}),
                'request_product_qty' : fields.integer('Request Qty',required =True,readonly=True, states={'draft': [('readonly', False)]}),
                'approved_qty' : fields.integer('Approved Qty',required =True,readonly=True, states={'draft': [('readonly', False)],'sent': [('readonly', False)]}),
                'request_id' : fields.many2one('request.product', 'Request Product'),
                'location_id': fields.many2one('stock.location', 'Request Location',required =True,readonly=True, states={'draft': [('readonly', False)]},domain=[('usage', '=', 'internal')]),
           #     'request_detail_line': fields.one2many('request.product.detail.line', 'request_line_id', 'Request Detail Lines',),
                'state': fields.selection([
                        ('draft', 'Draft'),
                        ('cancel', 'Cancelled'),
                        ('approved', 'Approved'),
                        ('progress', 'In Progress'),
                        ('sent','Request Sent'),
                        ('done','Done'),
                        ],'State',readonly=True, states={'draft': [('readonly', False)],'sent': [('readonly', False)]}),
                'parent_id': fields.many2one('request.product.line', 'Parent Request', select=True, ondelete='cascade'),
                'child_id': fields.one2many('request.product.line', 'parent_id', string='Child Product Request'),
                'parent_left': fields.integer('Left Parent', select=1),
                'parent_right': fields.integer('Right Parent', select=1),
               
               
                }    
    
    _defaults = {
         'state': 'draft',
         'location_id' : lambda self, cr, uid, context : context['location_id'] if context and 'location_id' in context else None,
         'approved_qty':1,
         'request_product_qty' : 1,
         
       } 
 
# class request_product_detail_line(osv.osv):
#     _name = "request.product.detail.line" 
#     
#     def _get_location_id(self, cr, uid, *args):
#           user_obj = self.pool.get('res.users').browse(cr,uid,uid)
#           if user_obj.location_id:
#              return user_obj.location_id.id
#           return False      
#       
#     _columns = {
#                 'product_id' : fields.many2one('product.product', 'Product'),
#                 'request_product_qty' : fields.integer('Request Qty'),
#                 'approved_qty' : fields.integer('Approved Qty'),
#                 'request_line_id' : fields.many2one('request.product.line', 'Request Product Line'),
#                 'request_id' : fields.many2one('request.product', 'Request Product'),
#                 'location_id': fields.many2one('stock.location', 'Request Location',),
#                 'state': fields.selection([
#                         ('draft', 'Draft'),
#                         ('cancel', 'Cancelled'),
#                         ('Approved', 'Approved'),
#                         ],'State')
#                 }    
#     
#     _defaults = {
#         'state': 'draft',
#          'location_id' : _get_location_id,
#        } 
    