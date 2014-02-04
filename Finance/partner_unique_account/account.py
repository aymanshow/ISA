import time
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _





class account_invoice(osv.osv):
    _inherit='account.invoice'
    _columns={
              'account_id': fields.many2one('account.account', 'Account', readonly=True, states={'draft':[('readonly',False)]}, help="The partner account used for this invoice."),
              }
    
    def action_date_assign(self, cr, uid, ids, *args):
        obj=self.browse(cr,uid,ids[0])
        if not obj.account_id.id:
            raise osv.except_osv(_('No Account!'),_("You Must Define An Account for this Partner'!") )
        for inv in self.browse(cr, uid, ids):
            res = self.onchange_payment_term_date_invoice(cr, uid, inv.id, inv.payment_term.id, inv.date_invoice)
            if res and res['value']:
                self.write(cr, uid, [inv.id], res['value'])
        return True
    