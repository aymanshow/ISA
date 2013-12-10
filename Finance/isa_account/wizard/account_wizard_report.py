# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.osv import fields, osv
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta




class account_report_general_ledger(osv.osv_memory):
    _inherit = "account.report.general.ledger"
    _name = "account.report.general.ledger"
    _description = "General Ledger Report"

    _columns = {
                'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
                }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['landscape',  'initial_balance', 'amount_currency', 'sortby','report_currency'])[0])
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})
        if data['form']['landscape']:
            return { 'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger_landscape_isa', 'datas': data}
        return { 'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger1', 'datas': data}
    
    
class account_balance_report(osv.osv_memory):
    _inherit = "account.balance.report"
    _name = 'account.balance.report'
    
    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }
    
    
    def _print_report(self, cr, uid, ids, data, context=None):
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['report_currency'])[0])
        return {'type': 'ir.actions.report.xml', 'report_name': 'account.account.balance.isa', 'datas': data}
    
class accounting_report(osv.osv_memory):
    _name = "accounting.report"
    _inherit = "accounting.report"
    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }
    
    
    def _print_report(self, cr, uid, ids, data, context=None):
        data['form'].update(self.read(cr, uid, ids, ['date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter','target_move','report_currency'], context=context)[0])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.financial.report.isa',
            'datas': data,
        }
        
        
    
    
    
class account_print_journal(osv.osv_memory):
    _inherit = "account.print.journal"
    _name = 'account.print.journal'
    
    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['sort_selection','report_currency'], context=context)[0])
        if context.get('sale_purchase_only'):
            report_name = 'account.journal.period.print.sale.purchase.isa'
        else:
            report_name = 'account.journal.period.print.isa'
        return {'type': 'ir.actions.report.xml', 'report_name': report_name, 'datas': data}
    
    
class account_general_journal(osv.osv_memory):
    _inherit = "account.general.journal"

    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }

    def _print_report(self, cr, uid, ids, data, context=None):
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['report_currency'], context=context)[0])
        return {'type': 'ir.actions.report.xml', 'report_name': 'account.general.journal.isa', 'datas': data}
    
    
class account_central_journal(osv.osv_memory):
    _inherit = "account.central.journal"
    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }

    def _print_report(self, cr, uid, ids, data, context=None):
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['report_currency'], context=context)[0])
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.central.journal.isa',
                'datas': data,
                }

class account_partner_balance(osv.osv_memory):
    _inherit = 'account.partner.balance'
    _name = 'account.partner.balance'
    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['display_partner','report_currency'])[0])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.partner.balance.isa',
            'datas': data,
            }

class account_partner_ledger(osv.osv_memory):
    _inherit = 'account.partner.ledger'
    _columns={
              'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
              }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['initial_balance', 'filter', 'page_split', 'amount_currency','report_currency'])[0])
        if data['form']['page_split']:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.third_party_ledger.isa',
                'datas': data,
        }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.third_party_ledger_other.isa',
                'datas': data,
        }


class account_aged_trial_balance(osv.osv_memory):
    _inherit = 'account.aged.trial.balance'
    _name = 'account.aged.trial.balance'
    _columns = {
                'report_currency': fields.selection([('base','Base Currency'),('usd','USD')],'Currency',required=True),
                }
    

    def _print_report(self, cr, uid, ids, data, context=None):
        res = {}
        if context is None:
            context = {}

        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['period_length', 'direction_selection','report_currency'])[0])

        period_length = data['form']['period_length']
        if period_length<=0:
            raise osv.except_osv(_('User Error!'), _('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise osv.except_osv(_('User Error!'), _('You must set a start date.'))

        start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")

        if data['form']['direction_selection'] == 'past':
            for i in range(5)[::-1]:
                stop = start - relativedelta(days=period_length)
                res[str(i)] = {
                    'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop - relativedelta(days=1)
        else:
            for i in range(5):
                stop = start + relativedelta(days=period_length)
                res[str(5-(i+1))] = {
                    'name': (i!=4 and str((i) * period_length)+'-' + str((i+1) * period_length) or ('+'+str(4 * period_length))),
                    'start': start.strftime('%Y-%m-%d'),
                    'stop': (i!=4 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop + relativedelta(days=1)
        data['form'].update(res)
        if data.get('form',False):
            data['ids']=[data['form'].get('chart_account_id',False)]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.aged_trial_balance.isa',
            'datas': data
        }

