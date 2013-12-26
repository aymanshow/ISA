from osv import osv
from osv import osv,fields
import openerp.addons.decimal_precision as dp
import time
from openerp.tools.translate import _
import purchase_requisition




class sale_order(osv.osv):
    _inherit = 'sale.order'
    _name = 'sale.order'
    _columns = {
                'pnl': fields.many2one('pnl.order', 'Related P&L'),
                'work_order':fields.binary('Work Order'),#Do not allow Sale Confirmation without a WORK ORDER
                'tech_proposal':fields.binary('Technical Proposal'),
                'comm_proposal':fields.binary('Commercial Proposal'),
                'comment': fields.text('Project Background', size=64),
                'cust_comment': fields.text('Customer Expectations', size=64),
                'solution_review': fields.text('Solution Review', size=64),
                'contract_review': fields.text('Project Background', size=64),
                'close_date': fields.date('Estimated Closing date'),
                'state': fields.selection([
                                           ('draft', 'Draft Quotation'),
                                           ('pnl', 'Draft PNL'),
                                           ('sent', 'Quotation Sent'),
                                           ('cancel', 'Cancelled'),
                                           ('waiting_date', 'Waiting Schedule'),
                                           ('progress', 'Sales Order'),
                                           ('manual', 'Sale to Invoice'),
                                           ('invoice_except', 'Invoice Exception'),
                                           ('meeting', 'Handover Meeting'),
                                           ('done', 'Done'),],
                                           'Status', readonly=True, track_visibility='onchange',
                                           help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True), #Set by default to 1 year 
                }
    
    # If Sale order is linked to a P&L -> Add a state: P&L. The product fields should not be editable in this state.            }
    #def generate_handover_meeting(self, cr, uid, ids, context=context):
     #Create the Handover Meeting as a new Step in the Sale Order Workflow. All Sales order that are in the Handover Meeting State must be present in a separate view.
#     def generate_project(self,cr,uid,ids, context=None):
#         #(1) [Pending]New Project (2) [Done]Create Analytical Accounts for the Project 
#         #(3) Create Analytical Accounts for the P&L lines (4) Create the Project Budget based on the P&L
#         #TASK: CREATE a sequence for Projects
#         obj=self.browse(cr,uid,ids[0])
#         analytic_parent = self.pool.get('account.analytic.account').search(cr,uid,[('name','=','Projects'),('type','=','view')])
#         analytical_dict={
#             'name': obj.name,
#             'active': True,
#             'type': 'contract',
#             'parent_id':analytic_parent[0]
#             #'state': 'open',
#             #'priority': 1,
#             #'sequence': 10,
#             #'alias_model': 'project.task',
#             #'privacy_visibility': 'employees',
#             #'alias_domain': False,  # always hide alias during creation
#                       }
#         project_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,analytical_dict,context=context)
#                 
#         #Creation of Budget
#         budget_dict = {'name':"Budget for:" + obj.name ,
#                        'code':obj.name,
#                        'date_from':obj.date_order,
#                        'date_to':obj.close_date,
#                        }
#         budget_id = self.pool.get('crossovered.budget').create(cr, uid, budget_dict, context=context)
#         #Creation of Analytical Lines and corresponding budget lines
#         for vals in obj.pnl.line_ids:
#             budget_line_ids = {}
#             equip_dict = {'name': vals.name, 
#                           'active': True, 
#                           'type': 'normal', 
#                           'parent_id':project_analytic_id,}
#             analy_id = self.pool.get('account.analytic.account').create(cr,uid,equip_dict,context=context)
#             budget_line_dict ={
#                                    'crossovered_budget_id': budget_id,
#                                    'analytic_account_id': analy_id,
#                                    'general_budget_id': 2,
#                                    'date_from': obj.date_order, 
#                                    'date_to':obj.close_date,
#                                    'planned_amount': -  vals.amount,
#                                    }
#             self.pool.get('crossovered.budget.lines').create(cr, uid, budget_line_dict, context=context)
    def action_button_confirm(self, cr, uid, ids, context=None):
        super(sale_order, self).action_button_confirm(cr, uid, ids, context) 
        
        obj=self.browse(cr,uid,ids[0])
        if not obj.close_date:
             raise osv.except_osv(_('Can not Confirm Order!'),
                                         _('Please Define Estimated Closing Date First.')) 
             return False
        self.pool.get('sale.order').write(cr,uid,obj.id,{'state':'progress'})
        if obj.pnl:
            self.pool.get('pnl.order').write(cr,uid,obj.pnl.id,{'state':'done'})
        return True       
        
    def handover_project(self,cr,uid,ids,context=None):
        vals={}
        if isinstance(ids, (list, tuple)):
            ids=ids[0]
        obj=self.browse(cr,uid,ids)
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
                  'user_id':uid,
                  'partner_id':obj.partner_id.id,
                  }
            project_id=self.pool.get('project.project').create(cr,uid,vals)
            project_analytic_id=self.pool.get('project.project').browse(cr,uid,project_id).analytic_account_id.id
            #self.generate_project(cr,uid,ids,context=None)
            self.write(cr,uid,ids,{'state':'meeting'})
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
        
        
        
        return True
#HAVING ISSUES CREATING A PROJECT
#         project_dict = {'name': obj.name, 
#                         'state': 'open',
#                         'priority': 1,
#                         'sequence': 10,
#                         'alias_model': 'project.task',
#                         'privacy_visibility': 'employees',
#                         'alias_domain': False,  # always hide alias during creation
#             }
#         project_id = self.pool.get('account.analytic.account').project_create(cr,uid,project_analytic_id,project_dict)

        
        
class pnl_order(osv.osv):
    _name = "pnl.order"
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'cogs_total': 0.0,
                'cif_total': 0.0,
                'consul_total': 0.0,
                'service_cost': 0.0,
                'serv_rev':     0.0,
            }
            val = val1 = val2 =val3=val4=val5= 0.0
            #cur = order.pricelist_id.currency_id
            print "test"
            for line in order.line_ids:
               val += line.quote_amt
               val1 +=  line.cif_amt
               val2 +=  line.consultancy_amt
            p =0   
            for line1 in order.cogs_addl_costs:
                p += line1.perc
                   
            print "ttt",val,val1,val2,p
            val3 = val*(190-order.cogs_rev_perc)/100
            val4 = order.tax_perc*val3/100
            val5 = order.fund_perc*val/100
            
            res[order.id]['cogs_total']= val
            res[order.id]['cif_total']= val1
            res[order.id]['consul_total']= val2
            res[order.id]['cogs_rev'] = val3
            res[order.id]['tax_amt']  = val4
            res[order.id]['fund_amt']  = val5
            res[order.id]['cogs_gross_margin']  = val3 - (val+val1+val2+val4+val5)
            res[order.id]['cogs_total_costs'] =(val+val1+val2+val4+val5)+ (val3 - (val+val1+val2+val4+val5))*p/100
            res[order.id]['cogs_profit'] = val3- res[order.id]['cogs_total_costs']
            val6 =0
            for line in order.serv_line:
               val6 += line.subtotal
               
            p1 =0   
            for line1 in order.serv_addl_costs:
                p1 += line1.perc
            val7 = val6*(170-order.serv_rev_perc)/100
            val8 = val7*order.ser_tax_perc/100
            print "val1",val,val1
            res[order.id]['serv_rev']= val7
            res[order.id]['service_cost']= val6
            res[order.id]['serv_tax_amt']= val8
            res[order.id]['serv_gross_margin']= val7 - val6 -val8
            res[order.id]['serv_total_cost']=    val6+val8 + (val7 - val6 -val8)*p1/100
            res[order.id]['serv_profit'] = val7 - (val6+val8 + (val7 - val6 -val8)*p1/100) 
            res[order.id]['total_rev'] = res[order.id]['cogs_rev'] + res[order.id]['serv_rev']
            res[order.id]['total_costs'] = res[order.id]['cogs_total_costs'] + res[order.id]['serv_total_cost']
            res[order.id]['total_profit'] = res[order.id]['cogs_profit'] + res[order.id]['serv_profit']
            
            
        return res
    
#     def _net_amount(self, cr, uid, ids, field_name, arg, context=None):
#         res = {}
#         
#         for order in self.browse(cr, uid, ids, context=context):
#             res[order.id] = {
#                   'total_rev': order.cogs_rev + order.serv_rev,
#                   'total_costs': order.cogs_total_costs + order.serv_total_cost,
#                   'total_profit': order.cogs_profit + order.serv_profit, 
#             }
#         print "here1234", res
#         
#         
#         return res
            
#     def _amount_all1(self, cr, uid, ids, field_name, arg, context=None):
#         res = {}
#         
#         for order in self.browse(cr, uid, ids, context=context):
#             res[order.id] = {
#                 'service_cost': 0.0,
#                 'serv_rev':     0.0,
#             }
#             val = val1 = 0.0
#             for line in order.serv_line:
#                val += line.subtotal
#                
#             p =0   
#             for line1 in order.serv_addl_costs:
#                 p += line1.perc
#                    
#             val1 = val*(170-order.serv_rev_perc)/100
#             val2 = val1*order.ser_tax_perc/100
#             print "val1",val,val1
#             res[order.id]['serv_rev']= val1
#             res[order.id]['service_cost']= val
#             res[order.id]['serv_tax_amt']= val2
#             res[order.id]['serv_gross_margin']= val1 - val -val2
#             res[order.id]['serv_total_cost']=    val+val2 + (val1 - val -val2)*p/100
#             res[order.id]['serv_profit'] = val1 - (val+val2 + (val1 - val -val2)*p/100)
#         return res
    
    
    def _get_line(self, cr, uid, ids, context=None):
        result = {}
        print "ids",ids
        for line in self.pool.get('pnl.cogs.line').browse(cr, uid, ids, context=context):
            
            result[line.pnl_id.id] = True
        print "result",result    
        return result.keys()
    
    def _get_serv_line(self, cr, uid, ids, context=None):
        result = {}
        print "ids",ids
        for line in self.pool.get('pnl.serv.line').browse(cr, uid, ids, context=context):
            
            result[line.pnl_id.id] = True
        print "result",result    
        return result.keys()
    
    def _get_costs(self, cr, uid, ids, context=None):
        result = {}
        print "ids",ids
        for line in self.pool.get('pnl.add.costs').browse(cr, uid, ids, context=context):
            
            result[line.pnl_id.id] = True
        print "result",result    
        return result.keys()
    
   
    
    _columns = {
	'name' : fields.char('Reference'),
    
    'user_id': fields.many2one('res.users', 'User'),
#     'order_id':fields.many2one('sale.order', ''),
    'comment': fields.text('Comment', size=64),
    'posted_date': fields.datetime('Created Date'),
	'customer': fields.many2one('res.partner', 'Customer'),	
    
	'cogs_rev_perc': fields.float('Markup factor'),
	'tax_perc': fields.float('Tax Rate'),
	'fund_perc': fields.float('% for Funding'),
    
	'line_ids' : fields.one2many('pnl.cogs.line','pnl_id','Products to Purchase'),
	'cogs_addl_costs' : fields.one2many('pnl.add.costs.goods', 'pnl_id','Additional Costs',
                                        domain=[('type','=','goods')], context={'default_type':'goods'},),
	
	'serv_rev_perc': fields.float('Revenue factor'),
    'ser_tax_perc': fields.float('Service Tax Rate'),
	'serv_addl_costs' : fields.one2many('pnl.add.costs', 'pnl_id','Additional Costs',
                                        domain=[('type','=','service')], context={'default_type':'service'},),
	'serv_line' : fields.one2many('pnl.serv.line', 'pnl_id','Services'),
    
# 	'total_rev': fields.float('Total Revenue'),
#     'total_costs': fields.float('Total Costs'),
# 	'total_profit': fields.float('Total Profit'),
    
    'lead_id': fields.many2one('crm.lead','Opportunity'),
    
   
    
    'total_rev': fields.function(_amount_all, string='Total Revenue', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal',], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
    'total_costs': fields.function(_amount_all, string='Total Costs', type='float',
                               store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal',], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
     'total_profit': fields.function(_amount_all, string='Total Profit', type='float',
                               store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal',], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
                
                                       
                
                
                
    
    'serv_profit': fields.function(_amount_all, string='Profit (Service)', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal',], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
                
                
    'serv_total_cost': fields.function(_amount_all, string='Total Service Cost', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10), 
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10), 
                'pnl.serv.line': (_get_serv_line, ['subtotal',], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
                
    
     'serv_gross_margin': fields.function(_amount_all, string='Service Gross Margin', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
                
     'serv_tax_amt': fields.function(_amount_all, string='Service Tax Amount', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
                
    'serv_rev': fields.function(_amount_all, string='Revenue Quote', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                 'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
                
                
    'service_cost': fields.function(_amount_all, string='Total Cost of Implementation Service', type='float',
                                store={
                'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),  
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
                
    
    'cogs_profit': fields.function(_amount_all, string='Profit', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
                
    'cogs_total_costs': fields.function(_amount_all, string='Total Cost of Goods Sold', type='float',
                                store={
                'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
                
    'cogs_gross_margin': fields.function(_amount_all, string='Gross Margin', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
    
    'fund_amt': fields.function(_amount_all, string='Fund Amount', type='float',
                                store={
                'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
                
    'tax_amt': fields.function(_amount_all, string='Tax Amount', type='float',
                                store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
                
    'cogs_rev': fields.function(_amount_all, string='Revenue Quote', type='float',
                                 store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
                
                
                
     'cogs_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Cost of Goods',
            store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",  ),
    'cif_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total CIF',
            store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums", ),
    'consul_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Consultancy',
            store={
                 'pnl.order': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','cogs_rev_perc','fund_perc','tax_perc','cogs_addl_costs','serv_line','serv_rev_perc','ser_tax_perc','serv_addl_costs'], 10),  
                'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
                'pnl.serv.line': (_get_serv_line, ['subtotal'], 10),
                'pnl.add.costs': (_get_costs, ['perc'], 10),
            }, multi="sums",),
    'state': fields.selection([('draft', 'New'),('progress', 'Progress'),('negotiation', 'Negotiation'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status'),
    'budget_id':fields.many2one('crossovered.budget','Budget Id'),
        }
    
    
#     def write(self, cr, uid, ids, vals, context=None):
#         if vals['state']=='draft':
#             vals.update({'state': 'progress'})
#         return super(pnl_order, self).write(cr, uid, ids, vals, context=context)

    def _get_addl_cost(self, cr, uid, context=None):
        if context is None: context = {}
        print "context"
        list = [{'name' : 'Commissions',
                 'perc' : 4,
                 'type' : 'goods',
                 },

                {'name' : 'Shared Costs',
                 'perc' : 6,
                 'type' : 'goods',
                 },
                
                {'name' : 'G&A',
                 'perc' : 5,
                 'type' : 'goods',
                 },
                
                ]
       
        return list
    
    def _get_serv_addl_cost(self, cr, uid, context=None):
        if context is None: context = {}
        print "context"
        list = [{'name' : 'Commissions',
                 'perc' : 4,
                 'type' : 'service'
                 },
                
                {'name' : 'Shared Costs',
                 'perc' : 6,
                 'type' : 'service'
                 },
                
                {'name' : 'G&A',
                 'perc' : 5,
                 'type' : 'service'
                 },]
       
        return list
    
    _defaults = {
        'user_id'         : lambda self,cr,uid,context: uid,
        'posted_date'     : time.strftime('%Y-%m-%d %H:%M:%S'),
        'tax_perc'        : lambda self,cr,uid,context: 1,
        'fund_perc'       : lambda self,cr,uid,context:5,
        'cogs_addl_costs' : _get_addl_cost,
        'serv_addl_costs' : _get_serv_addl_cost,
        'ser_tax_perc' : lambda self,cr,uid,context: 1,
        'state':'draft',
            }
    
    def generate_quotation(self,cr,uid,ids,context):
        if ids:
            vals={}
            obj=self.browse(cr,uid,ids[0])
            prod_rev=obj.cogs_rev
            cifs_rev=obj.cif_total
            ser_rev=obj.serv_rev
            vals={
                  'name':'/',
                  'partner_id':obj.customer.id,
                  'date_order':obj.posted_date,
                  'picking_policy':'direct',
                  'order_policy':'manual',
                  'user_id':obj.user_id.id,
                  'shop_id':1,
                  'pricelist_id':1,
                  'partner_invoice_id':1,
                  'partner_shipping_id':1,
                  'invoice_quantity':'order',
                  'pnl':ids[0],
                  }
            
            order_id=self.pool.get('sale.order').create(cr,uid,vals)
            product_id2=self.pool.get('product.product').search(cr,uid,[('name','=','Services'),('type','=','service')])
            product_id1=self.pool.get('product.product').search(cr,uid,[('name','=','Products'),('type','=','service')])
            product_id3=self.pool.get('product.product').search(cr,uid,[('name','=','CIFS'),('type','=','service')])
            if not (product_id1 or product_id2 or product_id3):
                 raise osv.except_osv(_('Can not Proceed!'),
                                         _('Create The product Services and CIFS in products.')) 
            else:
                val1={'product_id':product_id1[0],
                      'product_uom' : 1,
                      'discount': 0.0,
                      'product_uom_qty': 1,
                      'product_uos_qty': 1,
                      'order_id':order_id,
                      'sequence': 10,
                      'state': 'draft',
                      'type': 'make_to_stock',
                      'price_unit': prod_rev,
                      'name':'Products',
                      }
                val2={'product_id':product_id2[0],
                      'product_uom' : 1,
                      'discount': 0.0,
                      'product_uom_qty': 1,
                      'product_uos_qty': 1,
                      'order_id':order_id,
                      'sequence': 10,
                      'state': 'draft',
                      'type': 'make_to_stock',
                      'price_unit': ser_rev,
                      'name':'Service',
                      }
                val3={'product_id':product_id3[0],
                      'product_uom' : 1,
                      'discount': 0.0,
                      'product_uom_qty': 1,
                      'product_uos_qty': 1,
                      'order_id':order_id,
                      'sequence': 10,
                      'state': 'draft',
                      'type': 'make_to_stock',
                      'price_unit': cifs_rev,
                      'name':'CIFS',
                      }
                self.pool.get('sale.order.line').create(cr,uid,val1)
                self.pool.get('sale.order.line').create(cr,uid,val2)
                self.pool.get('sale.order.line').create(cr,uid,val3)
                self.pool.get('sale.order').write(cr,uid,order_id,{'state':'pnl'})
                self.write(cr,uid,ids,{'state':'negotiation'})
                value = {'domain': str([('id', 'in', order_id)]),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sale.order',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name' : _('Quotation'),
                        'res_id': order_id,
                        }
        return value
    def update_quotation(self,cr,uid,ids,context=None):
        res={}
        sale_obj=self.pool.get('sale.order')
        sale_line=self.pool.get('sale.order.line')
        obj=self.browse(cr,uid,ids[0])
        order_id=sale_obj.search(cr,uid,[('pnl','=',obj.id),('state','=','pnl')])
        order_id1=sale_obj.search(cr,uid,[('pnl','=',obj.id),('state','!=','pnl')])
        
        if order_id:
            product_id2=self.pool.get('product.product').search(cr,uid,[('name','ilike','Ser'),('type','=','service')])
            product_id1=self.pool.get('product.product').search(cr,uid,[('name','ilike','Prod'),('type','=','service')])
            product_id3=self.pool.get('product.product').search(cr,uid,[('name','ilike','CIFS'),('type','=','service')])
            for val in sale_obj.browse(cr,uid,order_id[0]).order_line:
                if val.product_id.id in product_id1:
                    sale_line.write(cr,uid,val.id,{'price_unit': obj.cogs_rev,})
                if val.product_id.id in product_id2:
                    sale_line.write(cr,uid,val.id,{'price_unit': obj.serv_rev,})
                if val.product_id.id in product_id3:
                    sale_line.write(cr,uid,val.id,{'price_unit': obj.cif_total,})
            res = {'domain': str([('id', 'in', order_id)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Quotation'),
                    'res_id': order_id[0],
                }
        elif order_id1:
            res = {'domain': str([('id', 'in', order_id)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Quotation'),
                    'res_id': order_id[0],
                }
        return res
    def cancel_quotation(self,cr,uid,ids,context):
        if ids:
            self.write(cr,uid,ids[0],{'state':'cancel'})
    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def create(self, cr, uid, data, context=None):
        order_id = super(pnl_order, self).create(cr, uid, data, context=context)
        pnl_obj = self.browse(cr, uid, order_id, context=context)
        for line in pnl_obj.cogs_addl_costs:
            self.pool.get('pnl.add.costs').write(cr, uid,line.id,{'amount' : line.perc * pnl_obj.cogs_gross_margin/100})
        for line in pnl_obj.serv_addl_costs:
            self.pool.get('pnl.add.costs').write(cr, uid,line.id,{'amount' : line.perc * pnl_obj.serv_gross_margin/100})
#         pnl_dict = {
#                   'total_rev': pnl_obj.cogs_rev + pnl_obj.serv_rev,
#                   'total_costs': pnl_obj.cogs_total_costs + pnl_obj.serv_total_cost,
#                   'total_profit': pnl_obj.cogs_profit + pnl_obj.serv_profit,  
#                     }    
        #self.write(cr,uid,order_id,pnl_dict)            
        return order_id
    
    def write(self, cr, uid, ids, vals, context=None):
        super(osv.osv, self).write(cr, uid, ids, vals, context=context)
        #print "idsssssssssss11111111111111111",ids
        if isinstance(ids, (list, tuple)):
            ids=ids[0]
        #print "=================ids===========2",ids
        pnl_obj = self.browse(cr, uid, ids, context=context)
        if pnl_obj.state=='draft':
            self.write(cr,uid,ids,{'state':'progress'})
        if 'cogs_addl_costs' in vals:
            for l  in range(len(vals['cogs_addl_costs'])):  
                if vals['cogs_addl_costs'][l][2] != False and 'perc' in vals['cogs_addl_costs'][l][2]:
                  vals['cogs_addl_costs'][l][2]['amount'] = vals['cogs_addl_costs'][l][2]['perc']*pnl_obj.cogs_gross_margin/100
#       
        if 'serv_addl_costs' in vals:
            for l  in range(len(vals['serv_addl_costs'])):  
                if vals['serv_addl_costs'][l][2] != False and 'perc' in vals['serv_addl_costs'][l][2]:
                  vals['serv_addl_costs'][l][2]['amount'] = vals['serv_addl_costs'][l][2]['perc']*pnl_obj.serv_gross_margin/100
                             
        for line in pnl_obj.cogs_addl_costs:
            self.pool.get('pnl.add.costs').write(cr, uid,line.id,{'amount' : line.perc * pnl_obj.cogs_gross_margin/100})
            
        for line in pnl_obj.serv_addl_costs:
            self.pool.get('pnl.add.costs').write(cr, uid,line.id,{'amount' : line.perc * pnl_obj.serv_gross_margin/100})
            
#         pnl_dict = {
#                   'total_rev': pnl_obj.cogs_rev + pnl_obj.serv_rev,
#                   'total_costs': pnl_obj.cogs_total_costs + pnl_obj.serv_total_cost,
#                   'total_profit': pnl_obj.cogs_profit + pnl_obj.serv_profit,  
#                     }    
              
        return True
    
    

class pnl_cogs_line(osv.osv):
    _name = "pnl.cogs.line"
    
    def _overhead_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            #print "testing overhead",order.pnl_id.cogs_gross_margin
            res[order.id]= float(order.perc*order.pnl_id.cogs_gross_margin)/100
            
            #res[order.id] = order.tax_perc*order.cogs_rev/100
        return res
 
    
    def _compute_total(self,cr, uid,ids, field_name,args,context=None):
        res = {}
        for pnl_line in self.browse(cr, uid, ids, context=context):
            
            res[pnl_line.id] = pnl_line.cif_amt + pnl_line.consultancy_amt + pnl_line.quote_amt
        return res   
        
    def _get_quote_amt(self,cr,uid,ids,field_name,args,context):
        res={}
        amt=0.0
        for val in self.browse(cr,uid,ids):
            if val.type=='rfq' and val.quotation_id:
               amt=val.quotation_id.amount_total
            elif val.type=='tender' and val.requisition_id:
                for val1 in val.requisition_id.purchase_ids:
                    if val1.state == 'approved':
                        amt=val1.amount_total
        
        res[val.id]=amt
        
        return res 
    def _get_cif_amt(self,cr,uid,ids,field_name,args,context):
        res={}
        amt=0.0
        for val in self.browse(cr,uid,ids):
            if val.quotation_id:
               amt=val.quote_amt*val.perc_cif/100
            
        
        res[val.id]=amt
        
        return res    
    
    _columns = {
                'name' : fields.char('Equipment Name'),
	           'pnl_id' : fields.many2one('pnl.order','P&L', ondelete='cascade'),
               'type':fields.selection([('rfq','RFQs'),('tender','Tender')],'Type'),
               'requisition_id':fields.many2one('purchase.requisition','Tender'),
               'quotation_id' : fields.many2one('purchase.order','RFQs'),
	           'quote_amt' : fields.function(_get_quote_amt,type='float',string='Amount'), #Need to set it to a function = the amount from the quotation
                'perc_cif' : fields.float('CIF %'),
                'cif_amt' : fields.function(_get_cif_amt,type='float',string='CIF'),
                'consultancy_amt' : fields.float('Consultancy'),
                'amount': fields.function(_compute_total,string='Total'), #Function needs to be worked on and expanded
                }
    def onchange_quotation(self, cr, uid, ids, quotation_id):
        print "quotation_id",quotation_id
        if not quotation_id:
           result = {'value': {'quote_amt' : 0.0}}
        else:
            print "here"
            quot_obj = self.pool.get('purchase.order').browse(cr, uid, quotation_id)
            print "quot_obj",quot_obj,
            result = {'value': {'quote_amt' : quot_obj.amount_total}}
        
        return result
    
    
    def onchange_amount(self, cr, uid, ids, quote_amt,perc_cif):
        print "testing"
        if not perc_cif:
           result = {'value': {'cif_amt' : 0.0}}
        else:
            
            #quot_obj = self.pool.get('purchase.order').browse(cr, uid, quotation_id)
            
            result = {'value': {'cif_amt' : quote_amt*perc_cif/100}}
        
        return result
    
class pnl_add_costs(osv.osv):
    _name = "pnl.add.costs"
    
    def _overhead_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            #print "testing overhead",order.pnl_id.cogs_gross_margin
            res[order.id]= float(order.perc*order.pnl_id.cogs_gross_margin)/100
            
            #res[order.id] = order.tax_perc*order.cogs_rev/100
        return res
    
    def _get_pnl(self, cr, uid, ids, context=None):
        result = {}
        print "ids",ids
        for line in self.pool.get('pnl.order').browse(cr, uid, ids, context=context):
            
            result[line.id] = True
        print "result",result
        return result.keys()
    
    _columns = {
               'name' : fields.char('Description'),
        'pnl_id' : fields.many2one('pnl.order','P&L', ondelete='cascade'),
        'perc' : fields.float('Percentage'),
        'type' : fields.selection((('service','Service'),('goods','Goods')),'Type'),


        #'margin': fields.related('pnl_id', 'cogs_gross_margin', type="many2one", relation="pnl.order", string="Gross Margin", readonly=True,),
        
        'amount' : fields.float('Amount'),
        
        
#         'amount': fields.function(_overhead_amount, string='Amount', type='float',
#                                 store={
#                 # 'pnl.order': (_get_pnl, ['cogs_gross_margin',], 10),                      
#                  'pnl.add.costs': (lambda self, cr, uid, ids, c={}: ids, ['perc','pnl_id'], 10),                    
                # 'pnl.order': (_get_pnl, ['line_ids','cogs_rev_perc','fund_perc','tax_perc'], 10),  
               #  'pnl.cogs.line': (_get_line, ['quote_amt','cif_amt','consultancy_amt'], 10),
          #  } ), 
                }
    
class pnl_add_costs_service(osv.osv):
    _name = "pnl.add.costs.service"
    _inherit = "pnl.add.costs"
    _table = "pnl_add_costs"
    
    _defaults = {
                 'type' : 'service'
                 }    
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        return self.pool.get('pnl.add.costs').search(cr, user, args, offset, limit, order, context, count)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return self.pool.get('pnl.add.costs').read(cr, uid, ids, fields=fields, context=context, load=load)
class pnl_add_costs_goods(osv.osv):
    _name = "pnl.add.costs.goods"
    _inherit = "pnl.add.costs"
    _table = "pnl_add_costs"
    
    _defaults = {
                 'type' : 'goods'
                 } 
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        return self.pool.get('pnl.add.costs').search(cr, user, args, offset, limit, order, context, count)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return self.pool.get('pnl.add.costs').read(cr, uid, ids, fields=fields, context=context, load=load)   
        

class pnl_serv_line(osv.osv):
    _name ="pnl.serv.line"
    _columns = {
            'pnl_id' : fields.many2one('pnl.order','P&L', ondelete='cascade'),
            'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
            'product_id': fields.many2one('product.product', 'Product', domain=[('type','=','service')]),
            'product_qty': fields.float('Quantity'),
            'unit_price': fields.float('Unit Price'),
            'subtotal' :  fields.float('Subtotal'),
                }
    _defaults  = {
                 'product_qty': 1, 
                  }
    
    def onchange_product(self, cr, uid, ids, product_id, unit_price, product_qty,):
        print "product_id",product_id,unit_price,product_qty
        product_uom =False
        if product_id:
           product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
           if not unit_price:
              unit_price =  product_obj.list_price
           if not product_uom:
                 product_uom =  product_obj.uom_id.id  
                 
        result = {'value': {'product_id' : product_id,
                               'unit_price' : unit_price, 
                               'product_qty' : product_qty,
                               'subtotal': unit_price*product_qty,
                               'product_uom' : product_uom}}
        
        
        return result
    
class crm_lead(osv.osv):
    _name='crm.lead'
    _inherit='crm.lead'
    
    _columns={
              'seq_no':fields.char('Name',size=64),
              'pnl_id':fields.many2one('pnl.order','Pnl Order'),
              'state1':fields.selection([('draft','Draft'),('pnl','PNL')]),
              'salesperson':fields.many2one('hr.employee', 'Salesperson', size=64, domain="[('department_name','=','Sales')]"),
              }
    _defaults={
              'state1':'draft'
              }
    
    def view_pnl(self,cr,uid,ids,context=None):
        value={}
        list=[]
        if ids:
            obj=self.browse(cr,uid,ids[0])
            list.append(obj.pnl_id.id)
            value = {
                    'domain': str([('id', 'in', list)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pnl.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Profit & Loss'),
                    'res_id': list and list[0]
                }
            
            
            return value
        
class purchase_requisition(osv.osv):
    _inherit='purchase.requisition'
    _name='purchase.requisition'
    _columns={
              'pnl_ok':fields.boolean('PNL'),
              'exclusive': fields.selection([('exclusive','Purchase Requisition (exclusive)'),('multiple','Multiple Requisitions')],'Requisition Type', required=True,readonly=True, help="Purchase Requisition (exclusive):  On the confirmation of a purchase order, it cancels the remaining purchase order.\nPurchase Requisition(Multiple):  It allows to have multiple purchase orders.On confirmation of a purchase order it does not cancel the remaining orders"""),
              }
    _defaults={
               'exclusive':'exclusive',
               'pnl_ok':False,
               }
class purchase_order(osv.osv):
    _inherit='purchase.order'
    _columns={
              'pnl_ok':fields.boolean('PNL'),
              }