from osv import fields, osv
import datetime
from datetime import datetime, timedelta
import time
from tools.translate import _
import openerp.addons.decimal_precision as dp

class vehicle_accident_info(osv.osv):
    _name = "vehicle.accident.info"
    _description = "Resign Form"
    _columns = {
        'incident_no':fields.char('Incident No',size=64,readonly=True),
        'type': fields.selection([('major','Major'),
                                   ('minor','Minor')], 'Type'),
        'location':fields.char('Location',size=64),
        'date_time':fields.datetime('Date & Time'),
        'description':fields.text('Description'),
        'vehicle_detail_id':fields.many2one('fleet.vehicle','Vehicle Details'),
        'driver_name_id':fields.many2one('res.partner','Driver Name'),
        'odometer_value':fields.char('Odometer Value',size=64),
        'contact_details':fields.integer('Contact Details'),
        'witness_details':fields.char('Witness Name',size=64),
        'witness_contact_details':fields.integer('Contact Details'),
        'car_value':fields.integer('Car Value'),
        'remarks':fields.text('Remarks'),
        }
    _order = 'incident_no desc'
    _defaults={
               'incident_no': lambda obj, cr, uid, context: '/',
    }
    def on_change_vehicle(self, cr, uid, ids, vehicle_detail_id, context=None):
        if not vehicle_detail_id:
            return {}
        obj = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_detail_id, context=context)
        res_obj=self.pool.get('res.partner').browse(cr,uid,obj.driver_id.id,context=context)
        mobile=res_obj.mobile
        return {
            'value': {
                'driver_name_id':obj.driver_id.id,
                'car_value':obj.car_value,
                'odometer_value':obj.odometer,
                'contact_details':int(mobile)
            }
        }

    def create(self, cr, uid, vals, context=None):
        if vals.get('incident_no','/')=='/':
            vals['incident_no'] = self.pool.get('ir.sequence').get(cr, uid,'vehicle.accident.info') or '/'
        return super(vehicle_accident_info, self).create(cr, uid, vals, context=context)
    