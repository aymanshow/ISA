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

import account_cash_flow


""" 
There are two method for preparing Cash Flow statement.
1) Direct method 
2) Indirect method 
There are three section for the cash flow statement 
a) Operating Activities - which is most important one and calculation /presentation differ in two methods
b) Investing Activities 
c) Financial Activities

Now to get the data for the Operating ,as said , you can either use Direct method or Indirect method.
If you are using direct method , you dont need to compare balance sheet/income statement for the current period (period for which you want to print the cash flow report) and the previous period.But you need such comparison when you are using indirect method.
Doubt for Indirect method - will it take too much time to print the report as to prepare this report using indirect method ,first we get the data for the balance sheet and income statement for 2 period and apply calculation on those data. 
Drawback with direct method - most of the companies prefer Indirect method as in direct method you need to prepare schedule (?) similar to one used for the indirect method for operating activities to meet FASB requirements. So this is not the popular way and most software prefer Indirect method then direct method."""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

