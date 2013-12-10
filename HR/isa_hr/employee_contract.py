from osv import osv
from osv import fields
import time
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _

class employee_level(osv.osv):
    _name='employee.level'
    _columns={
        'name': fields.integer('Level',required=True),
        'minimum_amt': fields.integer('Minimum Amount',required=True),
        'maximum_amt': fields.integer('Maximum Amount',required=True),      
        }
class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _columns = {
                'level_ids': fields.many2one('employee.level','Level'),
                'wage': fields.integer('Wage', digits=(16,2), required=True, help="Basic Salary of the employee"),
    }
    
    def on_change_wage_level(self,cr,uid,ids,wage,context=None):
         if not wage:
            return {}
         res={}
         level_id=self.pool.get('employee.level').search(cr,uid,[('minimum_amt','<=',wage), ('maximum_amt', '>=', wage)], context=context)
         if not level_id:
             raise osv.except_osv(_('Warning!'), _('Level not found.'))
         res={
              'level_ids':level_id[0]
              }
         return {'value':res}
