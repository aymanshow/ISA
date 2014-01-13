from openerp.osv import fields, osv
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _
import datetime
import openerp.addons.decimal_precision as dp
from itertools import product



class receive_wizard(osv.osv_memory):
    _name='receive.wizard'
    def _get_total(self,cr,uid,ids,field_name,arg,context):
        res={}
        amount=0.0
        for val in self.browse(cr,uid,ids):
            amount=0.0
            for val1 in val.cashbox_line_ids:
                amount+=val1.sub_total
            res[val.id]=amount
        return res
    _columns={
              'department_id':fields.many2one('hr.department','Department',readonly=True),
              'journal_id':fields.many2one('account.journal','Journal',readonly=True),
              'amount':fields.integer('Amount',readonly=True),
              'cashbox_line_ids' : fields.one2many('account.cashbox.line.wizard', 'receive_id', 'CashBox'),
              'total':fields.function(_get_total,type='float',string='Received')
              }
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        list=[]
        res = super(receive_wizard, self).default_get(cr, uid, fields, context=context)
        if context['active_id']:
            obj = self.pool.get('payment.request').browse(cr, uid, context['active_id'], context=context)
            for val in obj.journal_id.cashbox_line_ids:
                list.append((0,2,{'pieces':val.pieces}))
            res.update({'amount': obj.amount_approve,'journal_id':obj.journal_id.id,'department_id':obj.department_id.id,'cashbox_line_ids':list})
        return res
    def receive(self,cr,uid,ids,context):
        obj=self.browse(cr,uid,ids[0])
        if obj.total != obj.amount:
            raise osv.except_osv(_('Warnig!'),_("Issued Amount and Received Amount is Not same"))
        
        date=str(datetime.date.today())
        register_id=self.pool.get('account.bank.statement').search(cr,uid,[('journal_id','=',obj.journal_id.id),('date','=',date),('state','in',['draft','open','approve']),('department_id','=',obj.department_id.id)])
        if register_id:
            register_obj=self.pool.get('account.bank.statement').browse(cr,uid,register_id[0])
            for val in obj.cashbox_line_ids: 
                for val1 in register_obj.details_ids:
                    if val.pieces == val1.pieces:
                        self.pool.get('account.cashbox.line').write(cr,uid,val1.id,{'number_opening':int(val1.number_opening)+int(val.number)})
                    else:
                        continue
        else:
            details_ids=[]
            for val in obj.cashbox_line_ids: 
                details_ids.append((0,2,{'pieces':val.pieces,'number_opening':val.number}))
            box={
                 'journal_id':obj.journal_id.id,
                 'date':date,
                 'department_id':obj.department_id.id,
                 'details_ids':details_ids
                 }
            register_id=self.pool.get('account.bank.statement').create(cr,uid,box)
        self.pool.get('payment.request').write(cr, uid, context['active_id'], {'state':'receive'})   
        return True
class account_cashbox_line_wizard(osv.osv_memory):
    _name = 'account.cashbox.line.wizard'
    _rec_name = 'pieces'
    def _sub_total(self, cr, uid, ids, name, arg, context=None):

        """ Calculates Sub total
        @param name: Names of fields.
        @param arg: User defined arguments
        @return: Dictionary of values.
        """
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'sub_total' : obj.pieces * obj.number,
            }
        return res
    _columns = {
        'pieces': fields.float('Unit Of Currency',readonly=True, digits_compute=dp.get_precision('Account')),
        'number':fields.integer('Number of Units',),
        'sub_total':fields.function(_sub_total, string='Opening Subtotal', type='float', digits_compute=dp.get_precision('Account'), multi='subtotal'),
        'receive_id' : fields.many2one('receive.wizard', 'Journal', select=1, ondelete="cascade"),
    }

    _order = 'pieces asc'
    def onchange_number(self,cr,uid,ids,pieces,number,context=None):
        res={}
        res={
             'sub_total':(pieces*number),
             }
        return {'value':res}
    