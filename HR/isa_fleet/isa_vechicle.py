from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
class isa_vechicle_maintenance(osv.osv):
    _name='isa.vehicle.maintenance'
    def create(self, cr, uid, vals, context=None):
        if not vals:
            vals = {}
        if context is None:
            context = {}
        vals['maintenance_id'] = self.pool.get('ir.sequence').get(cr, uid, 'isa.vehicle.maintenance')
        vals['maintenance_state']='pending'
        return super(isa_vechicle_maintenance, self).create(cr, uid, vals, context=context)
    _columns={
            'maintenance_id':fields.char('Maintenance Id',readonly=True),
            'category':fields.selection([('asset','Asset'),('vehicle','Vehicle')],'Category'),
            'vehicle_id':fields.many2one('fleet.vehicle','Vehicle'),
             'asset_id': fields.many2one('account.asset.asset', string='Asset'),

            'type':fields.selection([('s','Scheduled'),('b','Break Down'),('r','Regular'),('p','Preventive')],'Type'),
            'date_id':fields.datetime('Date & Time'),
            'spare_parts':fields.char('Spare Parts Used'),
            'maintenance_cost':fields.float('Maintenance Cost'),
            'maintenance_state':fields.selection([('draft','Draft'),('pending','Pending'),('done','Done')],'State'),
            'remark':fields.text('Remarks'),
            }
    _defaults = {
        'maintenance_state': 'draft',
                }
    def action_done(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids,{'maintenance_state':'done'})
        return True
    
    
   
isa_vechicle_maintenance() 
    