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
from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import time
import re



class wiz_appointment(osv.osv_memory):
    
    _name = 'wiz.appointment'
    _columns = {
                'user_id':fields.many2one('hr.employee','Responsible',required=True,readonly=True),
                'person':fields.char('Scheduled For',size=64,readonly=True),
                'company': fields.char('Company', size=64,readonly=True),
                'phone':fields.char('Phone Number',size=12,readonly=True),
                'name': fields.char('Subject', size=64,readonly=True),
                'address': fields.text('Address',readonly=True),
                'department':fields.many2one('hr.department','Department',readonly=True),
                'appointment_date': fields.datetime('Appointment Date/Time'),
                'end_date':  fields.datetime('End Date/Time'),
                'duration': fields.float('Duration'),
                }
    def onchange_calculate_hour(self,cr, uid, ids, start, end, context=None):
        res={}
        print "onchange date====================================",start,end,type(end),context
        if start and end:
            year1=int(start[:4])
            month1=int(start[5:7])
            day1=int(start[8:10])
            hour1=int(start[11:13])
            minute1=int(start[14:16])
            
            year2=int(end[:4])
            month2=int(end[5:7])
            day2=int(end[8:10])
            hour2=int(end[11:13])
            minute2=int(end[14:16])
            if year1==year2 and month1==month2 and day1==day2:
                
    #         start_date=datetime.datetime(year=year1, month=month1, day=day1, hour=hour1,minute=minute1)
    #         end_date=datetime.datetime(year=year2, month=month2, day=day2, hour=hour2,minute=minute2)
                if hour2>hour1 or hour2==hour1 and minute2>minute1:
                    
                    start_time=hour1*60+minute1
                    end_time=hour2*60+minute2
                    diff=(end_time-start_time)/60.0
                    print "====================================",diff
                    res={
                         'duration':diff
                         }
        
                return {'value':res}
        return res
    
    def default_get(self, cr, uid, fields, context=None):
        """
        Default get for name, opportunity_ids.
        If there is an exisitng partner link to the lead, find all existing
        opportunities links with this partner to merge all information together
        """
        res = super(wiz_appointment, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            tomerge = set([int(context['active_id'])])
            obj = self.pool.get('office.visitor').browse(cr, uid, int(context['active_id']), context=context)
            res.update({'user_id' : obj.to_whom.id,'person':obj.name,'company':obj.company,
                        'name':obj.reason,'phone':obj.phone,'department':obj.department.id,'address':obj.address})
 
        return res

    def make_appointment(self, cr, uid, ids, context):
        vals={}
        value={}
        list=[]
        if ids:
            obj=self.browse(cr,uid,ids[0])
            apt_no = self.pool.get('ir.sequence').get(cr, uid, 'shedule.meeting')
            vals={'name':apt_no,'user_id' : obj.user_id.id,'person':obj.person,'company':obj.company,
                        'subject':obj.name,'phone':obj.phone,'department':obj.department.id,'address':obj.address,'appointment_date':obj.appointment_date,
                        'end_date':obj.end_date,'duration':obj.duration}
            cr_id=self.pool.get('shedule.meeting').create(cr,uid,vals,context=context)
            print cr_id,'=============================9'
            list.append(cr_id)
            value = {
                    'domain': str([('id', 'in', list)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'shedule.meeting',
                    'view_id': list[0],
                    'type': 'ir.actions.act_window',
                    #'name' : _('Profit & Loss'),
                    'res_id': list[0]
                }
            return value
    
    
class wizard_approve(osv.osv):
    _name = "wizard.approve"

    
    _columns = {
        'name':fields.char('Appointment No',size=64,readonly=True),
        'user_id':fields.many2one('hr.employee','Responsible',required=True),
        'person':fields.char('Scheduled For',size=64),
        'company': fields.char('Company', size=64),
        'phone':fields.char('Phone Number',size=12),
        'subject': fields.char('Subject', size=64),
         'address': fields.text('Address'),
         'department':fields.many2one('hr.department','Department'),
         'appointment_date': fields.datetime('Appointment Date/Time'),
         'end_date':fields.datetime('End Date/Time'),
         'duration': fields.float('Duration'),
          'appointment': fields.selection([('no', 'No'), ('yes', 'Yes')], 'Taken Appointment'),
          'given_by': fields.many2one('hr.employee','Taken By'),
          'state': fields.selection([('draft', 'Pending'), ('approved', 'Approved'), ('cancel', 'Cancelled')], 'Status'),
        }
    
    def default_get(self, cr, uid, fields, context=None):
        """
        Default get for name, opportunity_ids.
        If there is an exisitng partner link to the lead, find all existing
        opportunities links with this partner to merge all information together
        """
        res = super(wizard_approve, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            print "active id============================",context['active_id']
            tomerge = set([int(context['active_id'])])
            obj = self.pool.get('shedule.meeting').browse(cr, uid, int(context['active_id']), context=context)
            print "obj=====================",obj
            res.update({'user_id' : obj.user_id.id,'person':obj.person,'company':obj.company,'subject':obj.subject,
                        'name':obj.name,'department':obj.department.id,'address':obj.address,'phone':obj.phone,
                        'appointment_date':obj.appointment_date,'end_date':obj.end_date,'duration':obj.duration})
 
        return res
    
    def approve(self,cr,uid,ids,context=None):
        
        print "ids================================",ids,context['active_id']
        obj=self.browse(cr,uid,ids[0])
        print "wiz obj========================",obj
        self.pool.get('shedule.meeting').write(cr,uid,context['active_id'],{'state': 'approved','appointment_date':obj.appointment_date,
                                                'end_date':obj.end_date,'duration':obj.duration},context)
        
        return True