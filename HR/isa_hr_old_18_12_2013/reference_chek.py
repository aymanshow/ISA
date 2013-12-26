from osv import osv
from osv import fields
import time
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext
class reference_check(osv.osv):
    _name="reference.check"
    _columns={
              'name':fields.char('Name'),
              'reference_check_ids':fields.one2many('refer.chk','rf_id','Reference Check'),
               'state_id':fields.many2one('hr.recruitment.stage','Recruitment Stage'),
              }
class refer_chk(osv.osv):
    _name='refer.chk'
    def get_serial_no(self, cr, uid, ids, name, arg, context={}):
        res = {}
        count=1
        for each in self.browse(cr, uid, ids):
            res[each.id]=count
            count+=1
        return res
    _columns={
              'serial_number' : fields.function(get_serial_no,type='integer',method=True,string='Sr.No'),
              'type':fields.selection([('1','Personal'),('2','Corporate')],'Type'),
              'name':fields.char('Name'),
              'phone_num':fields.char('Phone Number'),
              'email':fields.char('Email-Id'),
              'company':fields.char('Company'),
              'check_mode':fields.selection([('T','Telephonic'),('P','Personal'),('E','Email')],'Check Mode'),
              'feedback':fields.text('Feed Back'),
              'rf_id':fields.many2one('reference.check','Reference'),
              }
