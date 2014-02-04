from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import time
import re


class account_create(osv.osv_memory):
    _name='account.create'
    
    _columns={
              'name':fields.char('Account Name',required=True),
              'code':fields.char('Account Code',readonly=True),
              'portuguese_name':fields.char('Portuguese Name',required=True),
              'user_type': fields.many2one('account.account.type', 'Account Type', required=True),
              'type': fields.selection([ ('view', 'View'),
            ('other', 'Regular'),
            ('receivable', 'Receivable'),
            ('payable', 'Payable'),
            ('liquidity','Liquidity'),
            ('consolidation', 'Consolidation'),
            ('closed', 'Closed'),
        ], 'Internal Type', required=True, ),
              
              
              }
    _defaults={
              'type': 'other',
              }
    def default_get(self, cr, uid, fields, context=None):
        res = super(account_create, self).default_get(cr, uid, fields, context=context)
        obj = self.pool.get('account.invoice').browse(cr,uid,context['active_id'])
        if obj.account_id.id:
            raise osv.except_osv(_('Warning!'),_("Can not Create Account! Account is already Defined for this Partner!") )
        return res
    
    def create_account(self,cr,uid,ids,context):
        vals={}
        obj=self.browse(cr,uid,ids[0])
        invoice_obj=self.pool.get('account.invoice').browse(cr,uid,context['active_id'])
        if invoice_obj.account_id.id or invoice_obj.partner_id.property_account_payable.id:
            raise osv.except_osv(_('Warning!'),_("Can not Create Account! Account is already Defined for this Partner!") )
        else:
            code=self.pool.get('ir.sequence').get(cr, uid, 'account.account')
            vals={
                  'name':obj.name,
                  'code':code,
                  'portuguese_name':obj.portuguese_name,
                  'user_type':obj.user_type.id,
                  'type':obj.type,
                  }
            account_id=self.pool.get('account.account').create(cr,uid,vals),
        if not invoice_obj.partner_id.id:
            raise osv.except_osv(_('No Partner!'),_("Please Select a Partner to Create account'!") )
        else:
            self.pool.get('account.invoice').write(cr,uid,invoice_obj.id,{'account_id':account_id})
            self.pool.get('res.partner').write(cr,uid,invoice_obj.id,{'property_account_payable':account_id,'property_account_receivable':account_id})
        return True
    
    
    