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
from osv import osv
from osv import fields

class account_account(osv.osv):
    _inherit = "account.account"
    
    _columns = {
        'cash_flow_type': fields.selection([('operating', 'Operating Activities'), 
                        ('investing', 'Investing Activities'), 
                        ('financial', 'Financing Activities'),], 
                        'Cash Flow Type', help="""Set here the cash flow type that will be used to generate the cash flow financial statement."""),
        }

account_account()
