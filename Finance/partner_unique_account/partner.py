from osv import fields, osv

class res_partner(osv.osv):
     _name = 'res.partner'
     _inherit = 'res.partner'
     _description = 'Partner'
     
     _columns={
               'property_account_payable':fields.many2one('account.account','Account Payable',),
               'property_account_receivable':fields.many2one('account.account','Account Receivable'),
               }
     def onchange_partner(self,cr,uid,ids,property_account_payable,property_account_receivable,context=None):
         res={}
         if property_account_payable:
            res={
                'property_account_receivable':property_account_payable
                }
            return {'value':res}
         if property_account_receivable:
             res={
                'property_account_payable':property_account_receivable
                }
         
             return {'value':res}
         return res
     
         
     