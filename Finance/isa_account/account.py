from openerp.addons.base_status.base_stage import base_stage
import crm
from datetime import datetime
from operator import itemgetter
from openerp.osv import fields, osv, orm
import time
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext
import openerp.addons.decimal_precision as dp


class base_usd(osv.osv):
    _name='base.usd'
    _columns={
              'name':fields.char('Name',readonly=True),
              'amount':fields.float('Equivalent Amount'),
              }
    _defaults={
               'name':'USD Rate'
               
               }

class account_account(osv.osv):
    _inherit='account.account'
    def _set_credit_debit(self, cr, uid, account_id, name, value, arg, context=None):
        if context.get('config_invisible', True):
            return True

        account = self.browse(cr, uid, account_id, context=context)
        diff = value - getattr(account,name)
        if not diff:
            return True

        journal_obj = self.pool.get('account.journal')
        jids = journal_obj.search(cr, uid, [('type','=','situation'),('centralisation','=',1),('company_id','=',account.company_id.id)], context=context)
        if not jids:
            raise osv.except_osv(_('Error!'),_("You need an Opening journal with centralisation checked to set the initial balance."))

        period_obj = self.pool.get('account.period')
        pids = period_obj.search(cr, uid, [('special','=',True),('company_id','=',account.company_id.id)], context=context)
        if not pids:
            raise osv.except_osv(_('Error!'),_("There is no opening/closing period defined, please create one to set the initial balance."))

        move_obj = self.pool.get('account.move.line')
        move_id = move_obj.search(cr, uid, [
            ('journal_id','=',jids[0]),
            ('period_id','=',pids[0]),
            ('account_id','=', account_id),
            (name,'>', 0.0),
            ('name','=', _('Opening Balance'))
        ], context=context)
        if move_id:
            move = move_obj.browse(cr, uid, move_id[0], context=context)
            move_obj.write(cr, uid, move_id[0], {
                name: diff+getattr(move,name)
            }, context=context)
        else:
            if diff<0.0:
                raise osv.except_osv(_('Error!'),_("Unable to adapt the initial balance (negative value)."))
            nameinv = (name=='credit' and 'debit') or 'credit'
            move_id = move_obj.create(cr, uid, {
                'name': _('Opening Balance'),
                'account_id': account_id,
                'journal_id': jids[0],
                'period_id': pids[0],
                name: diff,
                nameinv: 0.0
            }, context=context)
        return True
    def __compute(self, cr, uid, ids, field_names, arg=None, context=None,
                  query='', query_params=()):
        """ compute the balance, debit and/or credit for the provided
        account ids
        Arguments:
        `ids`: account ids
        `field_names`: the fields to compute (a list of any of
                       'balance', 'debit' and 'credit')
        `arg`: unused fields.function stuff
        `query`: additional query filter (as a string)
        `query_params`: parameters for the provided query string
                        (__compute will handle their escaping) as a
                        tuple
        """
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
            'balance_usd': "COALESCE(SUM(l.debit_usd),0) - COALESCE(SUM(l.credit_usd), 0) as balance_usd",
            'debit_usd': "COALESCE(SUM(l.debit_usd), 0) as debit_usd",
            'credit_usd': "COALESCE(SUM(l.credit_usd), 0) as credit_usd",
            
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END FROM account_account WHERE id IN (l.account_id)) as foreign_balance",
        }
        #get all the necessary accounts
        children_and_consolidated = self._get_children_and_consol(cr, uid, ids, context=context)
        #compute for each account the balance/debit/credit from the move lines
        accounts = {}
        res = {}
        null_result = dict((fn, 0.0) for fn in field_names)
        if children_and_consolidated:
            aml_query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)

            wheres = [""]
            if query.strip():
                wheres.append(query.strip())
            if aml_query.strip():
                wheres.append(aml_query.strip())
            filters = " AND ".join(wheres)
            # IN might not work ideally in case there are too many
            # children_and_consolidated, in that case join on a
            # values() e.g.:
            # SELECT l.account_id as id FROM account_move_line l
            # INNER JOIN (VALUES (id1), (id2), (id3), ...) AS tmp (id)
            # ON l.account_id = tmp.id
            # or make _get_children_and_consol return a query and join on that
            request = ("SELECT l.account_id as id, " +\
                       ', '.join(mapping.values()) +
                       " FROM account_move_line l" \
                       " WHERE l.account_id IN %s " \
                            + filters +
                       " GROUP BY l.account_id")
            params = (tuple(children_and_consolidated),) + query_params
            cr.execute(request, params)

            for row in cr.dictfetchall():
                accounts[row['id']] = row

            # consolidate accounts with direct children
            children_and_consolidated.reverse()
            brs = list(self.browse(cr, uid, children_and_consolidated, context=context))
            sums = {}
            currency_obj = self.pool.get('res.currency')
            while brs:
                current = brs.pop(0)
#                can_compute = True
#                for child in current.child_id:
#                    if child.id not in sums:
#                        can_compute = False
#                        try:
#                            brs.insert(0, brs.pop(brs.index(child)))
#                        except ValueError:
#                            brs.insert(0, child)
#                if can_compute:
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    for child in current.child_id:
                        if child.company_id.currency_id.id == current.company_id.currency_id.id:
                            sums[current.id][fn] += sums[child.id][fn]
                        else:
                            sums[current.id][fn] += currency_obj.compute(cr, uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)

                # as we have to relay on values computed before this is calculated separately than previous fields
                if current.currency_id and current.exchange_rate and \
                            ('adjusted_balance' in field_names or 'unrealized_gain_loss' in field_names):
                    # Computing Adjusted Balance and Unrealized Gains and losses
                    # Adjusted Balance = Foreign Balance / Exchange Rate
                    # Unrealized Gains and losses = Adjusted Balance - Balance
                    adj_bal = sums[current.id].get('foreign_balance', 0.0) / current.exchange_rate
                    sums[current.id].update({'adjusted_balance': adj_bal, 'unrealized_gain_loss': adj_bal - sums[current.id].get('balance', 0.0)})

            for id in ids:
                res[id] = sums.get(id, null_result)
        else:
            for id in ids:
                res[id] = null_result
        return res
    
    
    
    _columns={
              'debit_usd':fields.function(__compute, fnct_inv=_set_credit_debit, digits_compute=dp.get_precision('Account'), string='Debit USD', multi='balance'),
              'credit_usd':fields.function(__compute, fnct_inv=_set_credit_debit, digits_compute=dp.get_precision('Account'), string='Credit USD', multi='balance'),
              'balance_usd': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Balance USD', multi='balance'),
              
              }
class account_move_line(osv.osv):
    _inherit='account.move.line'
    def _balance_usd(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        c = context.copy()
        c['initital_bal'] = True
        sql = """SELECT l2.id, SUM(l1.debit_usd-l1.credit_usd)
                    FROM account_move_line l1, account_move_line l2
                    WHERE l2.account_id = l1.account_id
                      AND l1.id <= l2.id
                      AND l2.id IN %s AND """ + \
                self._query_get(cr, uid, obj='l1', context=c) + \
                " GROUP BY l2.id"

        cr.execute(sql, [tuple(ids)])
        return dict(cr.fetchall())
    def _balance_search_usd(self, cursor, user, obj, name, args, domain=None, context=None):
        if context is None:
            context = {}
        if not args:
            return []
        where = ' AND '.join(map(lambda x: '(abs(sum(debit_usd-credit_usd))'+x[1]+str(x[2])+')',args))
        cursor.execute('SELECT id, SUM(debit_usd-credit_usd) FROM account_move_line \
                     GROUP BY id, debit_usd, credit_usd having '+where)
        res = cursor.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]
    
    def _query_get(self, cr, uid, obj='l', context=None):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalperiod_obj = self.pool.get('account.period')
        account_obj = self.pool.get('account.account')
        fiscalyear_ids = []
        if context is None:
            context = {}
        initial_bal = context.get('initial_bal', False)
        company_clause = " "
        if context.get('company_id', False):
            company_clause = " AND " +obj+".company_id = %s" % context.get('company_id', False)
        if not context.get('fiscalyear', False):
            if context.get('all_fiscalyear', False):
                #this option is needed by the aged balance report because otherwise, if we search only the draft ones, an open invoice of a closed fiscalyear won't be displayed
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, [])
            else:
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft')])
        else:
            #for initial balance as well as for normal query, we check only the selected FY because the best practice is to generate the FY opening entries
            fiscalyear_ids = [context['fiscalyear']]
 
        fiscalyear_clause = (','.join([str(x) for x in fiscalyear_ids])) or '0'
        state = context.get('state', False)
        where_move_state = ''
        where_move_lines_by_date = ''
 
        if context.get('date_from', False) and context.get('date_to', False):
            if initial_bal:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date < '" +context['date_from']+"')"
            else:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date >= '" +context['date_from']+"' AND date <= '"+context['date_to']+"')"
 
        if state:
            if state.lower() not in ['all']:
                where_move_state= " AND "+obj+".move_id IN (SELECT id FROM account_move WHERE account_move.state = '"+state+"')"
        if context.get('period_from', False) and context.get('period_to', False) and not context.get('periods', False):
            if initial_bal:
                period_company_id = fiscalperiod_obj.browse(cr, uid, context['period_from'], context=context).company_id.id
                first_period = fiscalperiod_obj.search(cr, uid, [('company_id', '=', period_company_id)], order='date_start', limit=1)[0]
                context['periods'] = fiscalperiod_obj.build_ctx_periods(cr, uid, first_period, context['period_from'])
            else:
                context['periods'] = fiscalperiod_obj.build_ctx_periods(cr, uid, context['period_from'], context['period_to'])
        if context.get('periods', False):
            if initial_bal:
                query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s)) %s %s" % (fiscalyear_clause, where_move_state, where_move_lines_by_date)
                period_ids = fiscalperiod_obj.search(cr, uid, [('id', 'in', context['periods'])], order='date_start', limit=1)
                if period_ids and period_ids[0]:
                    first_period = fiscalperiod_obj.browse(cr, uid, period_ids[0], context=context)
                    ids = ','.join([str(x) for x in context['periods']])
                    query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s) AND date_start <= '%s' AND id NOT IN (%s)) %s %s" % (fiscalyear_clause, first_period.date_start, ids, where_move_state, where_move_lines_by_date)
            else:
                ids = ','.join([str(x) for x in context['periods']])
                query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s) AND id IN (%s)) %s %s" % (fiscalyear_clause, ids, where_move_state, where_move_lines_by_date)
        else:
            query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s)) %s %s" % (fiscalyear_clause, where_move_state, where_move_lines_by_date)
 
        if initial_bal and not context.get('periods', False) and not where_move_lines_by_date:
            #we didn't pass any filter in the context, and the initial balance can't be computed using only the fiscalyear otherwise entries will be summed twice
            #so we have to invalidate this query
            raise osv.except_osv(_('Warning!'),_("You have not supplied enough arguments to compute the initial balance, please select a period and a journal in the context."))
        if context.get('journal_ids', False):
            query += ' AND '+obj+'.journal_id IN (%s)' % ','.join(map(str, context['journal_ids']))
 
        if context.get('chart_account_id', False):
            child_ids = account_obj._get_children_and_consol(cr, uid, [context['chart_account_id']], context=context)
            query += ' AND '+obj+'.account_id IN (%s)' % ','.join(map(str, child_ids))
 
        query += company_clause
        return query
    
    
    
    def _get_move_lines(self, cr, uid, ids, context=None):
        result = []
        for move in self.pool.get('account.move').browse(cr, uid, ids, context=context):
            for line in move.line_id:
                result.append(line.id)
        return result
    def _amount_usd(self,cr,uid,ids,field_name,arg,context):
        res={}
        amount=0.0
        for val in self.browse(cr,uid,ids):
            amount=float(val.debit/val.move_id.rate_usd)
            res[val.id]=amount
        return res
    def _amount_usd_credit(self,cr,uid,ids,field_name,arg,context):
        res={}
        amount=0.0
        for val in self.browse(cr,uid,ids):
            amount=float(val.credit/val.move_id.rate_usd)
            res[val.id]=amount
        return res
    _columns={
              'rate_usd': fields.related('move_id','rate_usd', string='USD Rate', type='float' ,
                                store = {
                             'account.move' : (_get_move_lines, ['rate_usd',], 20)
                                }),
              'debit_usd':fields.function(_amount_usd,type='float',digits_compute=dp.get_precision('Account'),string='Debit USD',store=True),
              'credit_usd':fields.function(_amount_usd_credit,type='float',digits_compute=dp.get_precision('Account'),string='Credit USD',store=True),
              'balance_usd': fields.function(_balance_usd, fnct_search=_balance_search_usd, string='Balance USD'),
              }
    _defaults={
               'debit_usd':0.0,
               'credit_usd':0.0
               }
    
    
#     def create(self, cr, uid, vals, context=None, check=True):
#         result = super(account_move_line, self).create(cr, uid, vals, context=context)
#         # CREATE Taxes
#         if vals.get('account_tax_id', False):
#             tax_id = tax_obj.browse(cr, uid, vals['account_tax_id'])
#             total = vals['debit'] - vals['credit']
#             if journal.type in ('purchase_refund', 'sale_refund'):
#                 base_code = 'ref_base_code_id'
#                 tax_code = 'ref_tax_code_id'
#                 account_id = 'account_paid_id'
#                 base_sign = 'ref_base_sign'
#                 tax_sign = 'ref_tax_sign'
#             else:
#                 base_code = 'base_code_id'
#                 tax_code = 'tax_code_id'
#                 account_id = 'account_collected_id'
#                 base_sign = 'base_sign'
#                 tax_sign = 'tax_sign'
#             tmp_cnt = 0
#             for tax in tax_obj.compute_all(cr, uid, [tax_id], total, 1.00, force_excluded=True).get('taxes'):
#                 #create the base movement
#                 if tmp_cnt == 0:
#                     if tax[base_code]:
#                         tmp_cnt += 1
#                         self.write(cr, uid,[result], {
#                             'tax_code_id': tax[base_code],
#                             'tax_amount': tax[base_sign] * abs(total)
#                         })
#                 else:
#                     data = {
#                         'move_id': vals['move_id'],
#                         'name': tools.ustr(vals['name'] or '') + ' ' + tools.ustr(tax['name'] or ''),
#                         'date': vals['date'],
#                         'partner_id': vals.get('partner_id',False),
#                         'ref': vals.get('ref',False),
#                         'account_tax_id': False,
#                         'tax_code_id': tax[base_code],
#                         'tax_amount': tax[base_sign] * abs(total),
#                         'account_id': vals['account_id'],
#                         'credit': 0.0,
#                         'debit': 0.0,
#                     }
#                     if data['tax_code_id']:
#                         self.create(cr, uid, data, context)
#                 #create the Tax movement
#                 data = {
#                     'move_id': vals['move_id'],
#                     'name': tools.ustr(vals['name'] or '') + ' ' + tools.ustr(tax['name'] or ''),
#                     'date': vals['date'],
#                     'partner_id': vals.get('partner_id',False),
#                     'ref': vals.get('ref',False),
#                     'account_tax_id': False,
#                     'tax_code_id': tax[tax_code],
#                     'tax_amount': tax[tax_sign] * abs(tax['amount']),
#                     'account_id': tax[account_id] or vals['account_id'],
#                     'credit': 40,
#                     'debit': 45,
#                     'debit_usd':789,
#                 }
#                 print "====tax line=======================create==============="
#                 if data['tax_code_id']:
#                     move_line_id=self.create(cr, uid, data, context)
#                 print "=========move_line_id============",move_line_id
#             del vals['account_tax_id']
# 
#         if check and ((not context.get('no_store_function')) or journal.entry_posted):
#             tmp = move_obj.validate(cr, uid, [vals['move_id']], context)
#             if journal.entry_posted and tmp:
#                 move_obj.button_validate(cr,uid, [vals['move_id']], context)
#         return result
    
    
    
    
    

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _get_amount(self, cr,uid,c):
         res=False
         val={}
         res=self.pool.get('base.usd').search(cr,uid,[('name','ilike','USD')])
         if res:
             obj=self.pool.get('base.usd').browse(cr,uid,res[0])
             return obj.amount
         return val
    _columns = {
                'rate_usd' : fields.float('USD Rate',required=True),
                }
    _defaults={ 
              'rate_usd':lambda self,cr,uid,c: self._get_amount(cr, uid, c),
              }
    
    
    def line_get_convert(self, cr, uid, x, part, date, context=None):
        print "==========line get convert===========",x
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', []),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
        }
    def group_lines(self, cr, uid, iml, line, inv):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if inv.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(inv, l)

                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    dam=am*inv.rate_usd
                    print "=============dam====================",dam
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['debit_usd'] = (dam > 0) and dam or 0.0
                    line2[tmp]['credit_usd'] = (dam < 0) and -dam or 0.0
                    line2[tmp]['tax_amount'] += l['tax_amount']
                    line2[tmp]['analytic_lines'] += l['analytic_lines']
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                line.append((0,0,val))
        return line
    
    def action_move_create(self, cr, uid, ids, context=None):
        
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
                    raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            acc_id = inv.account_id.id

            name = inv['name'] or inv['supplier_invoice_number'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
                'rate_usd': inv.rate_usd
            }
            
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
            
            
            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True
    
class account_voucher(osv.osv):
    _inherit = "account.voucher"
    def _get_amount(self, cr,uid,c):
         res=False
         val={}
         res=self.pool.get('base.usd').search(cr,uid,[('name','ilike','USD')])
         if res:
             obj=self.pool.get('base.usd').browse(cr,uid,res[0])
             return obj.amount
         return val
    _columns = {
                'rate_usd' : fields.float('USD Rate',required=True),
                }
    _defaults={ 
              'rate_usd':lambda self,cr,uid,c: self._get_amount(cr, uid, c),
              }
    def account_move_get(self, cr, uid, voucher_id, context=None):
        '''
        This method prepare the creation of the account move related to the given voucher.

        :param voucher_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        seq_obj = self.pool.get('ir.sequence')
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        if voucher.number:
            name = voucher.number
        elif voucher.journal_id.sequence_id:
            if not voucher.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            c = dict(context)
            c.update({'fiscalyear_id': voucher.period_id.fiscalyear_id.id})
            name = seq_obj.next_by_id(cr, uid, voucher.journal_id.sequence_id.id, context=c)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        if not voucher.reference:
            ref = name.replace('/','')
        else:
            ref = voucher.reference

        move = {
            'name': name,
            'journal_id': voucher.journal_id.id,
            'narration': voucher.narration,
            'date': voucher.date,
            'ref': ref,
            'period_id': voucher.period_id.id,
            'rate_usd':voucher.rate_usd,
        }
        return move
#     def proforma_voucher(self, cr, uid, ids, context=None):
#         self.action_move_line_create(cr, uid, ids, context=context)
#         return True
#     def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
#         '''
#         Return a dict to be use to create the first account move line of given voucher.
# 
#         :param voucher_id: Id of voucher what we are creating account_move.
#         :param move_id: Id of account move where this line will be added.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: mapping between fieldname and value of account move line to create
#         :rtype: dict
#         '''
#         voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
#         debit = credit = 0.0
#         # TODO: is there any other alternative then the voucher type ??
#         # ANSWER: We can have payment and receipt "In Advance".
#         # TODO: Make this logic available.
#         # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
#         if voucher.type in ('purchase', 'payment'):
#             credit = voucher.paid_amount_in_company_currency
#         elif voucher.type in ('sale', 'receipt'):
#             debit = voucher.paid_amount_in_company_currency
#         if debit < 0: credit = -debit; debit = 0.0
#         if credit < 0: debit = -credit; credit = 0.0
#         sign = debit - credit < 0 and -1 or 1
#         #set the first line of the voucher
#         move_line = {
#                 'name': voucher.name or '/',
#                 'debit': debit,
#                 'credit': credit,
#                 'debit_usd':debit*voucher.rate_usd,
#                 'credit_usd':credit*voucher.rate_usd,
#                 'account_id': voucher.account_id.id,
#                 'move_id': move_id,
#                 'journal_id': voucher.journal_id.id,
#                 'period_id': voucher.period_id.id,
#                 'partner_id': voucher.partner_id.id,
#                 'currency_id': company_currency <> current_currency and  current_currency or False,
#                 'amount_currency': company_currency <> current_currency and sign * voucher.amount or 0.0,
#                 'date': voucher.date,
#                 'date_maturity': voucher.date_due
#             }
#         return move_line
#     def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
#         '''
#         Create one account move line, on the given account move, per voucher line where amount is not 0.0.
#         It returns Tuple with tot_line what is total of difference between debit and credit and
#         a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).
# 
#         :param voucher_id: Voucher id what we are working with
#         :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
#         :param move_id: Account move wher those lines will be joined.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
#         :rtype: tuple(float, list of int)
#         '''
#         if context is None:
#             context = {}
#         move_line_obj = self.pool.get('account.move.line')
#         currency_obj = self.pool.get('res.currency')
#         tax_obj = self.pool.get('account.tax')
#         tot_line = line_total
#         rec_lst_ids = []
# 
#         date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
#         ctx = context.copy()
#         ctx.update({'date': date})
#         voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
#         voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
#         ctx.update({
#             'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
#             'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
#         prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
#         for line in voucher.line_ids:
#             #create one move line per voucher line where amount is not 0.0
#             # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
#             if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
#                 continue
#             # convert the amount set on the voucher line into the currency of the voucher's company
#             # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
#             amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
#             # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
#             # currency rate difference
#             if line.amount == line.amount_unreconciled:
#                 if not line.move_line_id:
#                     raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
#                 sign = voucher.type in ('payment', 'purchase') and -1 or 1
#                 currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
#             else:
#                 currency_rate_difference = 0.0
#                 
#             move_line = {
#                 'journal_id': voucher.journal_id.id,
#                 'period_id': voucher.period_id.id,
#                 'name': line.name or '/',
#                 'account_id': line.account_id.id,
#                 'move_id': move_id,
#                 'partner_id': voucher.partner_id.id,
#                 'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
#                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                 'quantity': 1,
#                 'credit': 0.0,
#                 'debit': 0.0,
#                 'debit_usd':0.0,
#                 'credit_usd':0.0,
#                 'date': voucher.date
#             }
#            
#             if amount < 0:
#                 amount = -amount
#                 if line.type == 'dr':
#                     line.type = 'cr'
#                 else:
#                     line.type = 'dr'
# 
#             if (line.type=='dr'):
#                 tot_line += amount
#                 move_line['debit'] = amount
#                 move_line['debit_usd'] = amount*voucher.rate_usd
#             else:
#                 tot_line -= amount
#                 move_line['credit'] = amount
#                 move_line['credit_usd'] = amount*voucher.rate_usd
# 
#             if voucher.tax_id and voucher.type in ('sale', 'purchase'):
#                 move_line.update({
#                     'account_tax_id': voucher.tax_id.id,
#                 })
# 
#             if move_line.get('account_tax_id', False):
#                 tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
#                 if not (tax_data.base_code_id and tax_data.tax_code_id):
#                     raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
# 
#             # compute the amount in foreign currency
#             foreign_currency_diff = 0.0
#             amount_currency = False
#             if line.move_line_id:
#                 # We want to set it on the account move line as soon as the original line had a foreign currency
#                 if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
#                     # we compute the amount in that foreign currency.
#                     if line.move_line_id.currency_id.id == current_currency:
#                         # if the voucher and the voucher line share the same currency, there is no computation to do
#                         sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
#                         amount_currency = sign * (line.amount)
#                     else:
#                         # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
#                         # otherwise we use the rates of the system
#                         amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
#                 if line.amount == line.amount_unreconciled:
#                     sign = voucher.type in ('payment', 'purchase') and -1 or 1
#                     foreign_currency_diff = sign * line.move_line_id.amount_residual_currency + amount_currency
# 
#             move_line['amount_currency'] = amount_currency
#             voucher_line = move_line_obj.create(cr, uid, move_line)
#             rec_ids = [voucher_line, line.move_line_id.id]
# 
#             if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
#                 # Change difference entry in company currency
#                 exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
#                 new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
#                 move_line_obj.create(cr, uid, exch_lines[1], context)
#                 rec_ids.append(new_id)
# 
#             if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
#                 # Change difference entry in voucher currency
#                 move_line_foreign_currency = {
#                     'journal_id': line.voucher_id.journal_id.id,
#                     'period_id': line.voucher_id.period_id.id,
#                     'name': _('change')+': '+(line.name or '/'),
#                     'account_id': line.account_id.id,
#                     'move_id': move_id,
#                     'partner_id': line.voucher_id.partner_id.id,
#                     'currency_id': line.move_line_id.currency_id.id,
#                     'amount_currency': -1 * foreign_currency_diff,
#                     'quantity': 1,
#                     'credit': 0.0,
#                     'debit': 0.0,
#                     'debit_usd':0.0,
#                     'credit_usd':0.0,
#                     'date': line.voucher_id.date,
#                 }
#                 new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
#                 rec_ids.append(new_id)
#             if line.move_line_id.id:
#                 rec_lst_ids.append(rec_ids)
#         return (tot_line, rec_lst_ids)
class account_move(osv.osv):
    _inherit = "account.move"
    
    def _get_amount(self, cr,uid,c):
         res=False
         val={}
         res=self.pool.get('base.usd').search(cr,uid,[('name','ilike','USD')])
         if res:
             obj=self.pool.get('base.usd').browse(cr,uid,res[0])
             return obj.amount
         return val
    
    _columns = {
                'rate_usd' : fields.float('USD Rate',required=True),
                }

    
    _defaults={
               'rate_usd':lambda self,cr,uid,c: self._get_amount(cr, uid, c),
               
               }
class account_bank_statement_line(osv.osv):
    _name = "account.bank.statement.line"
    _inherit='account.bank.statement.line' 
    _columns={
              
             'account_id': fields.many2one('account.account','Account',), 
             'state':fields.related('statement_id','state',type='selection',string='Status',required=True,selection=[('draft', 'New'),
                                   ('open','Open'), # used by cash statements
                                   ('approve','Approval'),
                                   ('confirm', 'Closed')]),
              
              }
    _defaults={
               'state':'draft',
               }    
class account_bank_statement(osv.osv):
    _name='account.bank.statement'
    _inherit='account.bank.statement'
    _columns={
              'state': fields.selection([('draft', 'New'),
                                   ('open','Open'), # used by cash statements
                                   ('approve','Approval'),
                                   ('confirm', 'Closed')],
                                   'Status', required=True, readonly="1",
                                   help='When new statement is created the status will be \'Draft\'.\n'
                                        'And after getting confirmation from the bank it will be in \'Confirmed\' status.'),
              
              'department_id':fields.many2one('hr.department','Department'),
              
              }
    def get_approve(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state':'approve'})
        return True
    
    
    def check_status_condition(self, cr, uid, state, journal_type='bank'):
        return state in ('draft','open','approve')
    
class account_cash_statement(osv.osv):
    _inherit = 'account.bank.statement'   
    def get_approve(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state':'approve'})
        return True



    
class payment_request(osv.osv):
    _name='payment.request'
    def _get_journal(self, cr, uid, context=None):
        journal_pool = self.pool.get('account.journal')
        res=journal_pool.search(cr, uid, [('type', '=', 'cash')],)
        return res and res[0] or False
    _columns={
              
              'department_id':fields.many2one('hr.department','Department'),
              'journal_id':fields.many2one('account.journal','Journal'),
              'amount':fields.integer('Requested Amount'),
              'account_from_id':fields.many2one('account.account','From Account'),
              'account_to_id':fields.many2one('account.account','To Account'),
              'amount_approve':fields.integer('Approved Amount'),
              'description':fields.char('Description For Cash'),
              'state': fields.selection([('draft', 'New'),
                                   ('waiting','Waiting'), # used by cash statements
                                   ('approve','Approved'),],
                                   'Status', required=True),
              'date':fields.date('Date'),
              
              }
    _defaults={
               'state':'draft',
               'journal_id':_get_journal,
               'date': lambda *a: time.strftime('%Y-%m-%d'),
               
               }
    def send_request(self,cr,uid,ids,context):
        self.write(cr,uid,ids,{'state':'waiting'})
        return True
    def approve(self,cr,uid,ids,context):
        self.write(cr,uid,ids,{'state':'approve'})
        return True
    
    
class hr_department(osv.osv):
    _inherit='hr.department'
    
    _columns={
              'issued_amount':fields.integer('Issued Amount'),
              }