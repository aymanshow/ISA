    def generate_project(self,cr,uid,ids, context=None):
        #(1) [Pending]New Project (2) [Done]Create Analytical Accounts for the Project 
        #(3) [Done]Create Analytical Accounts for the P&L lines (4) [Done]Create the Project Budget based on the P&L
        #TASK: CREATE a sequence for Projects
        obj=self.browse(cr,uid,ids[0])
        analytic_parent = self.pool.get('account.analytic.account').search(cr,uid,[('name','=','Projects'),('type','=','view')])
        analytical_dict={
            'name': obj.name,
            'active': True,
            'type': 'contract',
            'parent_id':analytic_parent[0]
            }
        project_analytic_id = self.pool.get('account.analytic.account').create(cr,uid,analytical_dict,context=context)
        """
        Structure of P&L Analy Accounts
        Products
            Cost of Goods Sold
            CIF
            Consulting
            Overheads
        Services
        Training
        """
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
        budget_dict = {'name':"Budget for: " + obj.name ,
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

