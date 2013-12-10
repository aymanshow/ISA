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
    
    def _duration(self, cr, uid, ids, field_name, arg, context=None):
            res = {}
            if not ids:
                return {}
            for val in self.browse(cr, uid, ids, context=context):
                diff=0.0
                start=val.appointment_date
                end=val.end_date
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
                        if hour2>hour1 or hour2==hour1 and minute2>minute1:
                            start_time=hour1*60+minute1
                            end_time=hour2*60+minute2
                            diff=(end_time-start_time)/60.0
                        else:
                            raise osv.except_osv(_('Can not Shedule appointment'),
                                                 _('Start time can not be more than or Same as End time'))
                        res[val.id] = diff
                        
                    else:
                        raise osv.except_osv(_('Can not schedule appointment'),
                                                 _('Start Date can not be more than End date'))
                
                return res
    
    
    
    _columns = {
                'user_id':fields.many2one('hr.employee','Responsible',required=True),
                'person':fields.char('Scheduled For',size=64),
                'company': fields.char('Company', size=64),
                'phone':fields.char('Phone Number',size=12),
                'name': fields.char('Subject', size=64),
                'department':fields.many2one('hr.department','Department'),
                'appointment_date': fields.datetime('Appointment Date/Time',required=True),
                'end_date':  fields.datetime('End Date/Time',required=True),
                'duration': fields.function(_duration, string='Duration', type='float'),
                }
    
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
                        'name':obj.reason,'phone':obj.phone,'department':obj.department.id,})
 
        return res

    def make_appointment(self, cr, uid, ids, context):
        vals={}
        if ids:
            obj=self.browse(cr,uid,ids[0])
            apt_no = self.pool.get('ir.sequence').get(cr, uid, 'shedule.meeting')
            vals={'name':apt_no,'user_id' : obj.user_id.id,'person':obj.person,'company':obj.company,
                        'subject':obj.name,'phone':obj.phone,'department':obj.department.id,'appointment_date':obj.appointment_date,
                        'end_date':obj.end_date,'duration':obj.duration}
            cr_id=self.pool.get('shedule.meeting').create(cr,uid,vals,context=context)
        
        
        return True
    
class reject_wiz(osv.osv_memory):
    _name='reject.wiz'
    _columns={
                  'reason':fields.text('Reason',required=True),
                  
                  }
    
    def reject(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        self.pool.get('shedule.meeting').write(cr,uid,context['active_id'],{'state': 'cancel','reason':obj.reason},context)
        
        return True
    
class reject_wiz1(osv.osv_memory):
    _name='reject.wiz1'
    _columns={
                  'reason':fields.text('Reason',required=True),
                  
            }
    def reject(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        self.pool.get('conference.booking').write(cr,uid,context['active_id'],{'state': 'cancel','reason':obj.reason},context)
        return True
    
class vehicle_reject_wiz(osv.osv_memory):
    _name='vehicle.reject.wiz'
    _columns={
                  'reason':fields.text('Reason',required=True),
                  
            }
    def reject(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        text=obj.reason
        self.pool.get('vehicle.choice').write(cr,uid,context['active_id'],{'state': 'cancel','manager_comment':text},context)
        return True
    


class action_done(osv.osv_memory):
    _name='action.done'
    _columns={
              'reason':fields.text('Feedback',required=True),
              }
    def done(self,cr,uid,ids,context=None):
        obj=self.browse(cr,uid,ids[0])
        self.pool.get('maintenace.master').write(cr,uid,context['active_id'],{'state': 'done','feedback':obj.reason},context)
        return True