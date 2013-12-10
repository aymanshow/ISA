from osv import fields,osv
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import time
import datetime
from openerp.tools.translate import _
from openerp import tools

class vehicle_choice(osv.osv):
    _name = 'vehicle.choice'

    def onchange_department(self,cr,uid,ids,employee,context=None):
        res={}
        if employee:
            hr_obj=self.pool.get('hr.employee').browse(cr, uid, employee)
            res={
                'department':hr_obj.department_id.id,
                'designation':hr_obj.job_id.id
                }
            return {'value':res}
#    def onchange_travel_type_drop(self,cr,uid,ids,drop,return1,context=None):
#        if not drop:
#            return {}
#        return {'value': {'return': False}}
#    
#    def onchange_travel_type_return(self,cr,uid,ids,drop,return1,context=None):
#        if not return1:
#            return {}
#        return {'value': {'drop': False,}}
#    
#    def _vehicle_name_get_manufacture(self, cr, uid, ids, prop, unknow_none, context=None):
#        res = {}
#        for record in self.pool.get('fleet.vehicle').browse(cr, uid, ids, context=context):
#            res[record.id] = record.model_id.brand_id.name
#        return res
    
    _columns ={
               'request_id':fields.char('Booking ID',size=64,readonly=True),
               'emp_name':fields.many2one('hr.employee','Name',required=True),
               'department':fields.many2one('hr.department','Department'),
               'designation': fields.many2one('hr.job','Designation'),
               'passenger_type': fields.selection([('employee', 'Employee'),
                                                   ('guest','Guest')],'Passenger',),
               'state': fields.selection([('draft', 'Draft'),
                          ('submit','Submitted'),
                          ('approved', 'Approved'), 
                          ('transport_dept', 'Transport Department'), 
                          ('complete', 'Completed'),
                          ('cancel','Rejected')], 'Status',),
               'guest_name':fields.char('Guest Name',size=64),
               'date':fields.datetime('Date & Time',required=True),
               'source':fields.char('Source Location',size=64,required=True),
               'destination':fields.char('Destination Location',size=64,required=True),
               'purpose_of_travel':fields.char('Purpose of Travel',size=64,required=True),
               'type': fields.selection([('drop', 'Drop'),
                          ('return', 'Return')], 'Type',required=True),
               'vehi_choice_id':fields.many2one('fleet.vehicle','Vehicle Details'),
               'odometer_start':fields.float('Odometer at Start'),
               'odometer_end':fields.float('Odometer at End'),
               'driver_name_id':fields.many2one('res.partner','Driver Name'),
               'contact_details':fields.integer('Contact Details'),
               'manager_comment':fields.text('Manager Comment'),
               
               'remark':fields.text('Remark'),
    }
    _order = 'request_id desc'
    _defaults={
               'state':'draft',
               'request_id': lambda obj, cr, uid, context: '/',
    }
    def default_get(self, cr, uid, fields, context=None):
        res = super(vehicle_choice, self).default_get(cr, uid, fields, context=context)
        emp_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not emp_id:
            raise osv.except_osv(_('Error!'), _('First create user as Employee!'))
        emp_obj = self.pool.get('hr.employee').browse(cr, uid, emp_id[0], context=context)
        res.update({'emp_name': emp_id[0],
                    'designation': emp_obj.job_id.id,
                    'department': emp_obj.department_id.id,
                    })
        return res

    def create(self, cr, uid, vals, context=None):
        if vals.get('request_id','/')=='/':
            vals['request_id'] = self.pool.get('ir.sequence').get(cr, uid, 'vehicle.choice') or '/'
            vals['state']='draft'
        emp_obj = self.pool.get('hr.employee').browse(cr, uid, uid, context=context)
        if vals.get('passenger_type')=='employee':
            if not emp_obj.job_id.id and not emp_obj.department_id.id:
                raise osv.except_osv(_('Error!'), _('First create the Job and Department of Employee'))
            elif not emp_obj.job_id.id:
                raise osv.except_osv(_('Error!'), _('First create the Job of Employee'))
            elif not emp_obj.department_id.id:
                raise osv.except_osv(_('Error!'), _('First create the Department of Employee'))
        else:
            if not vals.get('guest_name'):
                raise osv.except_osv(_('Error!'), _('First fill the Guest Name'))
            else:
                pass
        return super(vehicle_choice, self).create(cr, uid, vals, context=context)
    
    def action_submit(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state': 'submit'},context)
        return True
    def action_approve(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state': 'approved'},context)
        return True
    
    def action_send_for_transport(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state': 'transport_dept'},context)
        return True
    def action_complete(self,cr,uid,ids,context=None):
        vehicle_obj=self.browse(cr,uid,ids[0])
        
        if vehicle_obj.odometer_start < vehicle_obj.odometer_end:
            self.write(cr,uid,ids,{'state': 'complete'},context)
            return True
        else:
            raise osv.except_osv(
                        _('Error!'),
                        _('You cannot complete the vehicle booking application without filling odometer end value'))
        
    def on_change_driver(self, cr, uid, ids, vehi_choice_id, context=None):
        if not vehi_choice_id:
            return {}
        obj = self.pool.get('fleet.vehicle').browse(cr, uid, vehi_choice_id, context=context)
        res_obj=self.pool.get('res.partner').browse(cr,uid,obj.driver_id.id,context=context)
        mobile=res_obj.mobile
        return {
            'value': {
                'driver_name_id':obj.driver_id.id,
                'contact_details':int(mobile)
            }
        }
