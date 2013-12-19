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
import datetime
import pooler
from report import report_sxw
#from account.report import account_profit_loss
#from account.report import account_balance_sheet
from account.report.common_report_header import common_report_header
from tools.translate import _

class report_cash_flow(report_sxw.rml_parse, common_report_header):
    def __init__(self, cr, uid, name, context=None):
        super(report_cash_flow, self).__init__(cr, uid, name, context=context)
        self.obj_pl = account_profit_loss.report_pl_account_horizontal(cr, uid, name, context=context)
        self.obj_bs = account_balance_sheet.report_balancesheet_horizontal(cr, uid, name, context=context)
        self.result_sum = {'operating' : 0.0,
                           'investing' : 0.0,
                           'financial' : 0.0, }
        self.result = {}
        self.res_bl = {}
        self.result_temp = []
        self.localcontext.update({
            'time': time,
            'get_lines': self.get_lines,
            'get_lines_another': self.get_lines_another,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
            'get_data':self.get_data,
            'get_pl_balance':self.get_pl_balance,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_sortby': self._get_sortby,
            'get_filter': self._get_filter,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_company':self._get_company,
            'get_current_cash': self.get_current_cash,
            'get_financing_balance': self._get_financing_balance,
            'get_operating_balance': self._get_operating_balance,
            'get_adjusted_operating_balance': self._get_adjusted_operating_balance,
            
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(report_cash_flow, self).set_context(objects, data, new_ids, report_type=report_type)

    def _get_financing_balance(self):
        return self.result_sum['financial']

    def _get_adjusted_operating_balance(self):
        return self.result_sum['operating']

    def _get_adjusted_investing_balance(self):
        return self.result_sum['investing']

    def _get_operating_balance(self):
        operating_balance = self.result_sum['operating']
        if self.res_bl['type'] == _('Net Loss'):
            return self.res_bl['balance'] - operating_balance
        return operating_balance + self.res_bl['balance']

    def get_current_cash(self):
        return self._get_operating_balance() + self.result_sum['financial'] + self.result_sum['investing']

    def get_pl_balance(self):
        return self.res_bl['type'] ==_('Net Loss') and self.res_bl['balance']*-1 or self.res_bl['balance'] 
        
    def get_data(self,data):
        cr, uid = self.cr, self.uid
        db_pool = pooler.get_pool(self.cr.dbname)

#        Getting Profit or Loss Balance from profit and Loss report
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
        
        account_ids = account_pool._get_children_and_consol(cr, uid, account_id, context=ctx)
        accounts = account_pool.browse(cr, uid, account_ids, context=ctx)

        #Getting details from the balance sheet
        self.obj_bs.get_data(data)

        asset_list = self.obj_bs.result.get('asset',[])
        asset_dict = {}
        for account_dict in asset_list :
            asset_dict[account_dict['code']] = account_dict['balance']
            
        liability_list = self.obj_bs.result.get('liability', [])
        liability_dict = {}
        for account_dict in liability_list :
            liability_dict[account_dict['code']] = account_dict['balance']

        new_data = data.copy()
        if data['form']['filter'] == 'filter_no': 
            # hmm wat could b the cases  :-/ 
            fy_date_start = db_pool.get('account.fiscalyear').browse(cr, uid, data['form']['fiscalyear_id']).date_start
            new_data['form']['date_from'] = new_data['form']['date_to'] = fy_date_start
            new_data['form']['used_context']['date_to'] = new_data['form']['used_context']['date_from'] = fy_date_start
            new_data['form']['filter']='filter_date'
            
        elif data['form']['filter'] == 'filter_period': 
            # for the comparison it should take data for just previous period or starting to just previous period 
            # if it is starting from the previous then find the first period using date_start of period == date_start of fiscalyear
            # and period_to would be just previous period
            
            current_period_from = data['form']['period_from']
            account_period_obj = db_pool.get('account.period')
            account_period = account_period_obj.browse(cr, uid, current_period_from)
            period_start_date = datetime.datetime.strptime(account_period.date_start, '%Y-%m-%d')
            previous_period_date_stop = datetime.datetime.strftime(period_start_date - datetime.timedelta(1) , '%Y-%m-%d')
            fy_date_start = db_pool.get('account.fiscalyear').browse(cr, uid, data['form']['fiscalyear_id']).date_start

            # Need validation if it doesn't find any period - but if it s nt able to find then what would b the default date :-/
            previous_period_from = account_period_obj.search(cr, uid, [('date_start','=',fy_date_start)])[0]            
            previous_period_to = account_period_obj.search(cr, uid, [('date_stop','=',previous_period_date_stop)])[0]

            new_data['form']['period_from'] = new_data['form']['used_context']['period_from'] = previous_period_from
            new_data['form']['period_to'] = new_data['form']['used_context']['period_to'] = previous_period_to
            
        else:  #by date 
            # find the previous date of date_to and get the balance sheet form the date_start of fiscal year to the previous date : good :) 
            current_date_from = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d')
            previous_date_to = datetime.datetime.strftime(period_start_date - datetime.timedelta(1) , '%Y-%m-%d')
            
            fy_date_start = db_pool.get('account.fiscalyear').browse(cr, uid, data['form']['fiscalyear_id']).date_start

            new_data['form']['date_from'] = new_data['form']['used_context']['date_from'] = fy_date_start
            new_data['form']['date_to'] = new_data['form']['used_context']['date_to'] = previous_date_to
            
        self.obj_bs.get_data(new_data)
        previous_asset_list = self.obj_bs.result.get('asset', [])
        previous_liability_list = self.obj_bs.result.get('liability', [])
        previous_asset_dict = {}
        for account_dict in previous_asset_list :
            previous_asset_dict[account_dict['code']] = account_dict['balance']
        previous_liability_dict = {}
        for account_dict in previous_liability_list :
            previous_liability_dict[account_dict['code']] = account_dict['balance']

        new_data['form']['filter']='filter_no'
# I am doing something stupid with data - will check it latter on

        if not self.res_bl:
            self.res_bl['type'] = _('Net Profit')
            self.res_bl['balance'] = 0.0
        if self.res_bl['type'] == _('Net Profit'):
            self.res_bl['type'] = _('Net Profit')
        else:
            self.res_bl['type'] = _('Net Loss')

        for typ in types:
            accounts_temp = []
            for account in accounts:
                difference = 0.0
                if (account.cash_flow_type and account.cash_flow_type == typ):
                    account_dict = {
                        'id': account.id,
                        'code': account.code,
                        'name': account.name,
                        'level': account.level,
                    }
                    currency = account.currency_id and account.currency_id or account.company_id.currency_id
                    if account.code in asset_dict.keys() :
                        difference  = previous_asset_dict[account.code] - asset_dict[account.code]
                    if account.code in liability_dict.keys() :
                        difference  = previous_liability_dict[account.code] - liability_dict[account.code]
                    if account.type != 'view' :
                        self.result_sum[typ] += difference
                    account_dict.update({'balance' :difference })
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
