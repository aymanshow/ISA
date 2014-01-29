from osv import osv
from osv import osv,fields
import openerp.addons.decimal_precision as dp
import time
from openerp.tools.translate import _


class project_handover(osv.osv):
    _name='project.handover'
    _columns={
              'name':fields.char('Name'),
              'partner_id':fields.many2one('res.partner','Customer'),
              'order_id':fields.many2one('sale.order','Sale Order'),
              'pnl':fields.many2one('pnl.order','PNL'),
              'responsible':fields.many2one('res.users','Project Manager',required=True),
              'manger_id':fields.many2one('res.users','Business Development Team Manager'),
              'team_id':fields.many2one('crm.case.section','Sales Team'),
              'date':fields.date('Handover Date'),
              'team_manager':fields.many2one('res.users','Sales Team Manager'),
              'attachment_ids':fields.one2many('ir.attachment','handover_id','Document Attachment'),
              'state': fields.selection([('draft', 'New'),
                                   ('progress','In-Progress'),
                                   ('accept','Accepted'),('cancel','Rejected'),],
                                   'Status', required=True),
              
              }
    _defaults={
               'state':'draft',
               'date': lambda *a: time.strftime('%Y-%m-%d'),
               }
    def start_handover(self,cr,uid,ids,context):
        return self.write(cr,uid,ids,{'state':'progress'})
    def cancel(self,cr,uid,ids,context):
        return self.write(cr,uid,ids,{'state':'cancel'})
    def accept(self,cr,uid,ids,context):
        handover_obj=self.browse(cr,uid,ids[0])
        obj=handover_obj.order_id
        if not (obj.pnl and obj.partner_id):
             raise osv.except_osv(_('Can not Complete Handover!'),
                                         _('The sale order does not belong to any PNL'))
        else: 
            name=obj.pnl.name
            
            vals={
                  'name':obj.pnl.name,
                  'active': True,
                  'type': 'contract',
                  'use_tasks':True,
                  'state': 'draft',
                  'priority': 1,
                  'pnl':obj.pnl.id,
                  'sequence': 10,
                  'alias_model': 'project.task',
                  'privacy_visibility': 'employees',
                  'alias_domain': False,
                  'user_id':handover_obj.responsible.id if handover_obj.responsible else uid,
                  'partner_id':obj.partner_id.id,
                  }
            project_id=self.pool.get('project.project').create(cr,uid,vals)
            project_analytic_id=self.pool.get('project.project').browse(cr,uid,project_id).analytic_account_id.id
            #self.generate_project(cr,uid,ids,context=None)
            #self.write(cr,uid,ids,{'state':'meeting'})
            equip_dict = {'name': 'Products', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':project_analytic_id,}
            products_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'Cost of Goods Sold', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            cogs_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'CIF', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            cif_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'Consulting', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            consult_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)    
            equip_dict = {'name': 'Overheads', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':products_analytic_id,}
            overheads_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
    
            equip_dict = {'name': 'Service', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':project_analytic_id,}
            services_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            equip_dict = {'name': 'Cost of Services', 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':services_analytic_id,}
            cost_service_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            
            """Creation of Budget"""
            budget_dict = {'name':"Budget for: " + name ,
                           'code':obj.name,
                           'date_from':obj.date_order,
                           'date_to':obj.close_date,
                           }
            budget_id = self.pool.get('crossovered.budget').create(cr, uid, budget_dict, context=context)
            
            """"Creation of analytic accounts and budget lines for Product section of the P&L.""" 
            equip_dict = {
                          'name': 'Revenue', 
                          'active': True, 
                          'type': 'normal', 
                          'parent_id':products_analytic_id,
                          }
            analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            budget_line_dict ={
                           'crossovered_budget_id': budget_id,
                           'analytic_account_id': analy_id,
                           'general_budget_id': 1,
                           'date_from': obj.date_order, 
                           'date_to':obj.close_date,
                           'planned_amount': obj.pnl.cogs_rev,
                           }
            self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            
            """P&L COGS, CIF and Consulting"""
            for vals in obj.pnl.line_ids:
                
                equip_dict = {'name': vals.name, 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':cogs_analytic_id,}
                analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                budget_line_dict ={
                                       'crossovered_budget_id': budget_id,
                                       'analytic_account_id': analy_id,
                                       'general_budget_id': 2,
                                       'date_from': obj.date_order, 
                                       'date_to':obj.close_date,
                                       'planned_amount': -  vals.quote_amt,
                                       }
                self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
                
                if vals.cif_amt:
                    equip_dict = {'name': vals.name + " CIF", 
                                  'active': True, 
                                  'type': 'normal', 
                                  'parent_id':cif_analytic_id,}
                    analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                    budget_line_dict ={
                                           'crossovered_budget_id': budget_id,
                                           'analytic_account_id': analy_id,
                                           'general_budget_id': 2,
                                           'date_from': obj.date_order, 
                                           'date_to':obj.close_date,
                                           'planned_amount': -vals.cif_amt,
                                           }
                    self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
                if vals.consultancy_amt:
                    equip_dict = {'name': vals.name + " Consulting", 
                                  'active': True, 
                                  'type': 'normal', 
                                  'parent_id':consult_analytic_id,}
                    analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                    budget_line_dict ={
                                           'crossovered_budget_id': budget_id,
                                           'analytic_account_id': analy_id,
                                           'general_budget_id': 2,
                                           'date_from': obj.date_order, 
                                           'date_to':obj.close_date,
                                           'planned_amount': -vals.consultancy_amt,
                                           }
                    self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
             
            for vals in obj.pnl.cogs_addl_costs:
                budget_line_ids = {}
                equip_dict = {'name': vals.name, 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':overheads_analytic_id,}
                analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                budget_line_dict ={
                                       'crossovered_budget_id': budget_id,
                                       'analytic_account_id': analy_id,
                                       'general_budget_id': 2,
                                       'date_from': obj.date_order, 
                                       'date_to':obj.close_date,
                                       'planned_amount': -vals.amount,
                                       }
                self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            
            """"Creation of analytic accounts and budget lines for Services section of the P&L.""" 
            equip_dict = {
                          'name': 'Revenue', 
                          'active': True, 
                          'type': 'normal', 
                          'parent_id':services_analytic_id,
                          }
            analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
            budget_line_dict ={
                           'crossovered_budget_id': budget_id,
                           'analytic_account_id': analy_id,
                           'general_budget_id': 1,
                           'date_from': obj.date_order, 
                           'date_to':obj.close_date,
                           'planned_amount': obj.pnl.serv_rev,
                           }
            self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            
            for vals in obj.pnl.serv_line:
                budget_line_ids = {}
                equip_dict = {'name': vals.product_id.name, 
                              'active': True, 
                              'type': 'normal', 
                              'parent_id':cost_service_analytic_id,}
                analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
                budget_line_dict ={
                                       'crossovered_budget_id': budget_id,
                                       'analytic_account_id': analy_id,
                                       'general_budget_id': 2,
                                       'date_from': obj.date_order, 
                                       'date_to':obj.close_date,
                                       'planned_amount': -vals.subtotal,
                                       }
                self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
            self.pool.get('pnl.order').write(cr,uid,obj.pnl.id,{'budget_id':budget_id})
            self.pool.get('project.project').write(cr,uid,project_id,{'budget_id':budget_id})
            self.write(cr,uid,ids,{'project_id':project_id,'state':'accept'})
        return True
    
class ir_attachment(osv.osv):
    _inherit='ir.attachment'
    _columns={
              'handover_id':fields.many2one('project.handover','Handover'),
              }