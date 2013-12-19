# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

import pooler
from report import report_sxw
#from account.report import account_profit_loss
from account.report.common_report_header import common_report_header
from tools.translate import _

class report_cash_flow(report_sxw.rml_parse, common_report_header):
    def __init__(self, cr, uid, name, context=None):
        super(report_cash_flow, self).__init__(cr, uid, name, context=context)
        self.obj_pl = account_profit_loss.report_pl_account_horizontal(cr, uid, name, context=context)
        self.result_sum_operating = 0.0
        self.result_sum_financial = 0.0
        self.result = {}
        self.res_bl = {}
        self.result_temp = []
        self.localcontext.update({
            'time': time,
            'get_lines': self.get_lines,
            'get_lines_another': self.get_lines_another,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
            'sum_operating': self.sum_operating,
            'sum_financial': self.sum_financial,
            'get_data':self.get_data,
            'get_pl_balance':self.get_pl_balance,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_sortby': self._get_sortby,
            'get_filter': self._get_filter,
            'get_journal': self._get_journal,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_company':self._get_company,
            'get_target_move': self._get_target_move,
            'get_current_cash': self.get_current_cash
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(report_cash_flow, self).set_context(objects, data, new_ids, report_type=report_type)

    def sum_operating(self):
#        if self.res_bl['type'] == _('Net Profit'):
#            self.result_sum_dr += self.res_bl['balance']*-1
        return self.result_sum_operating

    def sum_financial(self):
#        if self.res_bl['type'] == _('Net Loss'):
#            self.result_sum_cr += self.res_bl['balance']
        return self.result_sum_financial

    def get_current_cash(self):
        return self.result_sum_operating + self.result_sum_financial

    def get_pl_balance(self):
        return self.res_bl['type'] =='Net Loss' and self.res_bl['balance']*-1 or self.res_bl['balance'] 
        
    def get_data(self,data):
        cr, uid = self.cr, self.uid
        db_pool = pooler.get_pool(self.cr.dbname)

        #Getting Profit or Loss Balance from profit and Loss report
        self.obj_pl.get_data(data)
        self.res_bl = self.obj_pl.final_result()

        account_pool = db_pool.get('account.account')
        currency_pool = db_pool.get('res.currency')

        types = [
            'operating',
            'investing',
            'financial'
        ]

        ctx = self.context.copy()
        ctx['fiscalyear'] = data['form'].get('fiscalyear_id', False)

        if data['form']['filter'] == 'filter_period':
            ctx['periods'] = data['form'].get('periods', False)
        elif data['form']['filter'] == 'filter_date':
            ctx['date_from'] = data['form'].get('date_from', False)
            ctx['date_to'] =  data['form'].get('date_to', False)
        ctx['state'] = data['form'].get('target_move', 'all')
        cal_list = {}
        pl_dict = {}
        account_dict = {}
        account_id = data['form'].get('chart_account_id', False)
        account_ids = account_pool._get_children_and_consol(cr, uid, account_id, context=ctx)
        accounts = account_pool.browse(cr, uid, account_ids, context=ctx)

        if not self.res_bl:
            self.res_bl['type'] = _('Net Profit')
            self.res_bl['balance'] = 0.0
        if self.res_bl['type'] == _('Net Profit'):
            self.res_bl['type'] = _('Net Profit')
        else:
            self.res_bl['type'] = _('Net Loss')
        pl_dict  = {
            'code': self.res_bl['type'],
            'name': self.res_bl['type'],
            'level': False,
            'balance':self.res_bl['balance'],
        }
            
        for typ in types:
            accounts_temp = []
            for account in accounts:
                if (account.cash_flow_type and account.cash_flow_type == typ):
                    account_dict = {
                        'id': account.id,
                        'code': account.code,
                        'name': account.name,
                        'level': account.level,
                        'balance':account.balance,
                    }
                    currency = account.currency_id and account.currency_id or account.company_id.currency_id
                    print "===================self.result_sum_operating===============",self.result_sum_operating
                    print account.user_type.report_type,account.name
                    if account.user_type.report_type == 'income' and account.type <> 'view':# and (account.debit <> account.credit):
                        self.result_sum_operating += abs(account.balance)
                    if account.user_type.report_type == 'expense' and account.type <> 'view':# and (account.debit <> account.credit):
                        self.result_sum_operating -= account.balance
                    if account.user_type.report_type == 'liability' and account.type <> 'view':# and (account.debit <> account.credit):
                        self.result_sum_financial += abs(account.balance)
#                    if account.user_type.report_type == 'asset' and account.type <> 'view' and (account.debit <> account.credit):
#                        self.result_sum_dr -= account.balance
#                    if data['form']['display_account'] == 'bal_movement':
#                        if currency_pool.is_zero(self.cr, self.uid, currency, account.credit) > 0 or currency_pool.is_zero(self.cr, self.uid, currency, account.debit) > 0 or currency_pool.is_zero(self.cr, self.uid, currency, account.balance) != 0:
#                            accounts_temp.append(account_dict)
#                    elif data['form']['display_account'] == 'bal_solde':
#                        if currency_pool.is_zero(self.cr, self.uid, currency, account.balance) != 0:
#                            accounts_temp.append(account_dict)
#                    else:
#                        accounts_temp.append(account_dict)
                    accounts_temp.append(account_dict)                        
            self.result[typ] = accounts_temp
            cal_list[typ]=self.result[typ]

        if cal_list:
            temp = {}
            for typ in types :
                for i in range(0,len(cal_list[typ]) ):
                    temp={
                          'code_%s'%typ : cal_list[typ][i]['code'],
                          'name_%s'%typ : cal_list[typ][i]['name'],
                          'level_%s'%typ : cal_list[typ][i]['level'],
                          'balance%s'%typ : cal_list[typ][i]['balance'],
                          }
                    self.result_temp.append(temp)
        return None

    def get_lines(self):
        return self.result_temp

    def get_lines_another(self, group):
        return self.result.get(group, [])

report_sxw.report_sxw('report.account.cash.flow', 'account.account',
    'addons/account_cash_flow/report/account_cash_flow.rml',parser=report_cash_flow,
    header='internal')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
