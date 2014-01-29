from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import time
import re


class crm_lead2opportunity_partner(osv.osv_memory):
    _description = 'Lead To Opportunity Partner'
    _inherit = 'crm.lead2opportunity.partner'
    
    
    def action_apply(self, cr, uid, ids, context=None):
        """
        Convert lead to opportunity or merge lead and opportunity and open
        the freshly created opportunity view.
        """
        if context is None:
            context = {}
        sequence=self.pool.get('ir.sequence').get(cr, uid, 'crm.lead')
        crm_id=context['active_id']
        
        w = self.browse(cr, uid, ids, context=context)[0]
        opp_ids = [o.id for o in w.opportunity_ids]
        if w.name == 'merge':
            lead_id = self.pool.get('crm.lead').merge_opportunity(cr, uid, opp_ids, context=context)
            lead_ids = [lead_id]
            lead = self.pool.get('crm.lead').read(cr, uid, lead_id, ['type'], context=context)
            if lead['type'] == "lead":
                context.update({'active_ids': lead_ids})
                self._convert_opportunity(cr, uid, ids, {'lead_ids': lead_ids}, context=context)
        else:
            lead_ids = context.get('active_ids', [])
            if crm_id:
                self.pool.get('crm.lead').write(cr,uid,crm_id,{'seq_no':sequence})
            self._convert_opportunity(cr, uid, ids, {'lead_ids': lead_ids}, context=context)

        return self.pool.get('crm.lead').redirect_opportunity_view(cr, uid, lead_ids[0], context=context)






class make_pnl_wiz(osv.osv_memory):
    
    _name = 'make.pnl.wiz'
    
    
    def _selectPartner(self, cr, uid, context=None):
        if context is None:
            context = {}
        lead_obj = self.pool.get('crm.lead')
        active_id = context and context.get('active_id', False) or False
        if not active_id:
            return False
        lead = lead_obj.read(cr, uid, active_id, ['partner_id'])
        return lead['partner_id']
    
    def _get_shop_id(self, cr, uid, ids, context=None):
        cmpny_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        shop = self.pool.get('sale.shop').search(cr, uid, [('company_id', '=', cmpny_id)])
        return shop and shop[0] or False
    
    _columns={
              'shop_id': fields.many2one('sale.shop', 'Shop', required=True),
              'partner_id': fields.many2one('res.partner', 'Customer', required=True, domain=[('customer','=',True)]),
              'close': fields.boolean('Mark Won', help='Check this to close the opportunity after having created the sales order.'),
              }
    
    _defaults = {
                'shop_id': _get_shop_id,
                'close': False,
                'partner_id': _selectPartner,
                }
    
    def makePnl(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # update context: if come from phonecall, default state values can pnl the quote crash lp:1017353
        context.pop('default_state', False)        
        
        case_obj = self.pool.get('crm.lead')
        pnl_obj = self.pool.get('pnl.order')
        partner_obj = self.pool.get('res.partner')
        data = context and context.get('active_ids', []) or []

        for pnl in self.browse(cr, uid, ids, context=context):
            partner = pnl.partner_id
            partner_addr = partner_obj.address_get(cr, uid, [partner.id],
                    ['default', 'invoice', 'delivery', 'contact'])
            pricelist = partner.property_product_pricelist.id
            fpos = partner.property_account_position and partner.property_account_position.id or False
            payment_term = partner.property_payment_term and partner.property_payment_term.id or False
            new_ids = []
            for case in case_obj.browse(cr, uid, data, context=context):
                if not partner and case.partner_id:
                    partner = case.partner_id
#                     fpos = partner.property_account_position and partner.property_account_position.id or False
#                     payment_term = partner.property_payment_term and partner.property_payment_term.id or False
#                     partner_addr = partner_obj.address_get(cr, uid, [partner.id],
#                             ['default', 'invoice', 'delivery', 'contact'])
#                     pricelist = partner.property_product_pricelist.id
#                 if False in partner_addr.values():
#                     raise osv.except_osv(_('Insufficient Data!'), _('No address(es) defined for this customer.'))

                vals = {
#                     'origin': _('Opportunity: %s') % str(case.id),
#                     'section_id': case.section_id and case.section_id.id or False,
                    'lead_id': case.id,
                    'customer': partner.id,
#                     'pricelist_id': pricelist,
#                     'partner_invoice_id': partner_addr['invoice'],
#                     'partner_shipping_id': partner_addr['delivery'],
#                     'date_order': fields.date.context_today(self,cr,uid,context=context),
#                     'fiscal_position': fpos,
#                     'payment_term':payment_term,
                    'name':case.seq_no
                }
                if partner.id:
                    vals['user_id'] = partner.user_id and partner.user_id.id or uid
                new_id = pnl_obj.create(cr, uid, vals, context=context)
                pnl_order = pnl_obj.browse(cr, uid, new_id, context=context)
                print "9800=============================",case.stage_id
                stage_id=self.pool.get('crm.case.stage').search(cr,uid,[('name','ilike','Profit'),('type','=','opportunity'),('state','=','open')])
                print "stage_id=========================",stage_id
                case_obj.write(cr, uid, [case.id], {'ref': 'sale.order,%s' % new_id,'pnl_id':new_id,'state1':'pnl',})
                case_obj.write(cr, uid, [case.id], {'ref': 'sale.order,%s' % new_id,'pnl_id':new_id,})
                new_ids.append(new_id)
                message = _("Opportunity has been <b>converted</b> to the PnL <em>%s</em>.") % (pnl_order.name)
                case.message_post(body=message)
            if pnl.close:
                case_obj.case_close(cr, uid, data)
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            if len(new_ids)<=1:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pnl.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Profit & Loss'),
                    'res_id': new_ids and new_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'pnl.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Profit & Loss'),
                    'res_id': new_ids
                }
            return value