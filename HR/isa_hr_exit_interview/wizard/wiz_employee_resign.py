from osv import fields, osv
import datetime
from datetime import datetime, timedelta
import time
from tools.translate import _
import openerp.addons.decimal_precision as dp

class employee_resign(osv.osv_memory):
    _name = "employee.resign"
    _description = "Resign Form"
    _columns = {
        'employee_id': fields.many2one('hr.employee','Employee'),
        'designation':fields.many2one('hr.job','Designation'),
        'department':fields.many2one('hr.department','Department'),
        'date_of_resign':fields.date('Date of Resigning'),
        'reason':fields.text('Reason'),
    }
    _defaults={
               'date_of_resign': fields.date.context_today,
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(employee_resign, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            hold = self.pool.get('hr.employee').browse(cr, uid, int(context['active_id']), context=context)
            res.update({'employee_id': hold.id,
                        'designation': hold.job_id.id,
                        'department': hold.department_id.id,
                        })
        else:
            pass
        return res
    
    def submit(self, cr, uid,ids,fields, context=None):
#        self.write(cr, uid, ids, {'state_for_appr': 'sent_for_approval'})
        return True
    
        