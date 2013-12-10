from osv import fields,osv
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import time
import datetime
from openerp.tools.translate import _
from openerp import tools

class office_visitor(osv.osv):
    _name = "office.visitor"
    _order = "id desc"
    _columns = {
        'apt_no':fields.many2one('shedule.meeting','Appointment No'),
        'visitor_no':fields.char('Visitor No',size=64,readonly=True),
        'name':fields.char('Full Name',size=64,required=True),
        'company': fields.char('Company', size=64,required=True),
        'address': fields.text('Address'),
        'phone':fields.char('Phone Number',size=12),
        'other': fields.text('Other Details'),
        'to_whom':fields.many2one('hr.employee','Whom To Meet'),
        'department':fields.many2one('hr.department','Department'),
        'in_time': fields.datetime('In Time',readonly=True),
        'out_time': fields.datetime('Out Time'),
        'reason': fields.char('Reason To Meet', size=124),
         'registration': fields.char('Registration Number', size=128),
         'model': fields.char('Model Number', size=128),
         'color': fields.char('Color', size=128),
         'laptop':fields.char('Laptop',size=128),
         'camera':fields.char('Camera',size=128),
         'storage':fields.char('Storage Device',size=128),
         'other_equip':fields.char('Other Equipment',size=128),
         'laptop_usage':fields.boolean('Laptop'),
         'camera_usage':fields.boolean('Camera'),
         'storage_usage':fields.boolean('Storage Device'),
         'other_equip_usage':fields.boolean('Other Equipment'),
         'laptop_disc':fields.char('Description',size=64),
         'camera_disc':fields.char('Description',size=64),
         'storage_disc':fields.char('Description',size=64),
         'other_disc':fields.char('Description',size=64),
         'appointment': fields.selection([('no', 'No'), ('yes', 'Yes')], 'Taken Appointment'),
         'given_by': fields.many2one('hr.employee','Taken By'),
         'state': fields.selection([('draft', 'New'),('in', 'Check-In'), ('out', 'Check-Out')], 'Status'),
        }
    
    
    def create(self, cr, uid, vals, context=None):
         vals['visitor_no'] = self.pool.get('ir.sequence').get(cr, uid, 'office.visitor')
         return super(office_visitor, self).create(cr, uid, vals, context=context)
     
    def check_in(self, cr, uid, ids, context=None):
         in_time=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
         self.write(cr,uid,ids,{'in_time': in_time,'state':'in'},context)
         return True
    def check_out(self, cr, uid, ids, context=None):
        if ids:
             obj=self.browse(cr,uid,ids)[0]
             if not obj.out_time:
                 in_time=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
             else:
                 in_time=obj.out_time
             self.write(cr,uid,ids,{'out_time': in_time,'state':'out'},context)
             return True
    def onchange_department(self,cr,uid,ids,employee,context=None):
        res={}
        if employee:
            hr_obj=self.pool.get('hr.employee').browse(cr, uid, employee)
            res={
                'department':hr_obj.department_id.id
                }
         
            return {'value':res}
     
     
     
     
    _defaults={
              'in_time'  : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
              'state' : 'draft'
               }
    
class shedule_meeting(osv.osv):
    _name = "shedule.meeting"
    _order = "id desc"
    
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
                            raise osv.except_osv(_('Can not Schedule appointment'),
                                                 _('Start time can not be more than or Same as End time'))
                        res[val.id] = diff
                        
                    else:
                        raise osv.except_osv(_('Can not Schedule appointment'),
                                                 _('Date Can Not Be More than one Day'))
                
                #res[val.id] = result.days
            return res

    
    _columns = {
        'name':fields.char('Appointment No',size=64,readonly=True),
        'user_id':fields.many2one('hr.employee','Responsible',required=True),
        'person':fields.char('Scheduled For',size=64),
        'company': fields.char('Company', size=64),
        'phone':fields.char('Phone Number',size=12),
        'subject': fields.char('Subject', size=64),
         'reason':fields.text('Reason For Rejection'),
         'department':fields.many2one('hr.department','Department'),
         'appointment_date': fields.datetime('Start Date/Time', required=True),
         'end_date': fields.datetime('End Date/Time',required=True),
         'duration': fields.function(_duration, string='Duration', type='float'),
          'appointment': fields.selection([('no', 'No'), ('yes', 'Yes')], 'Taken Appointment'),
          'given_by': fields.many2one('hr.employee','Taken By'),
          'state': fields.selection([('draft', 'Pending'), ('approved', 'Approved'), ('cancel', 'Cancelled')], 'Status',),
          }
    
    _defaults={
               'state':'draft',
               }
    def create(self, cr, uid, vals, context=None):
         vals['apt_no'] = self.pool.get('ir.sequence').get(cr, uid, 'shedule.meeting')
         return super(shedule_meeting, self).create(cr, uid, vals, context=context)
    
    
    def approve(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state': 'approved'},context)
        return True



class conference_master(osv.osv):
    _name = 'conference.master'
    _order = "id desc"

    _columns ={
               'room_id':fields.char('Room ID',size=64,readonly=True),
               'name':fields.char('Name',size=64),
               'capacity':fields.integer('Capacity'),
               'description': fields.text('Description'),
               }
    def create(self, cr, uid, vals, context=None):
         vals['room_id'] = self.pool.get('ir.sequence').get(cr, uid, 'conference.master')
         return super(conference_master, self).create(cr, uid, vals, context=context)
    
    _defaults={

               }


class conference_booking(osv.osv):
    _name = 'conference.booking'
    _order = "id desc"
    
    def _duration(self, cr, uid, ids, field_name, arg, context=None):
            res = {}
            if not ids:
                return {}
            for val in self.browse(cr, uid, ids, context=context):
                diff=0.0
                start=val.date
                end=val.end_date
                if start and end:
                    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                    from_dt = datetime.datetime.strptime(start, DATETIME_FORMAT)
                    to_dt = datetime.datetime.strptime(end, DATETIME_FORMAT)
                    if to_dt>from_dt:
                        timedelta = to_dt - from_dt
                        diff =  float(timedelta.seconds) /3600
                        res[val.id] = diff
                    else:
                        raise osv.except_osv(_('Can not Schedule appointment'),
                                                 _('Date Can Not Be More than one Day'))
                
            return res

    _columns ={
               'request_id':fields.char('Booking ID',size=64,readonly=True),
               'purpose':fields.char('Purpose',size=64,required=True),
               'emp_name':fields.many2one('hr.employee','Name',required=True),
               'department':fields.many2one('hr.department','Department',required=True),
               'designation': fields.many2one('hr.job','Designation',required=True),
               'room':fields.many2one('conference.master','Room Choice',required=True),
               'date':fields.datetime('Date Time',required=True),
               'end_date':fields.datetime('End Date Time',required=True),
               'alternate_date':fields.datetime('Alternate Date'),
               'priority':fields.selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], 'Priority',),
               'state': fields.selection([('draft', 'Draft'),('pending', 'Pending'), ('approved', 'Approved'), ('cancel', 'Rejected')], 'Status',),
               'duration': fields.function(_duration, string='Duration', type='float',readonly="true"),
               'reason':fields.text('Reason For Rejection'),
               }
    def create(self, cr, uid, vals, context=None):
         vals['request_id'] = self.pool.get('ir.sequence').get(cr, uid, 'conference.booking')
         vals['state']='pending'
         return super(conference_booking, self).create(cr, uid, vals, context=context)
    def onchange_department(self,cr,uid,ids,employee,context=None):
        res={}
        if employee:
            hr_obj=self.pool.get('hr.employee').browse(cr, uid, employee)
            res={
                'department':hr_obj.department_id.id,
                'designation':hr_obj.job_id.id
                }
         
            return {'value':res}
    def approve(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state': 'approved'},context)
        return True
     
     
    _defaults={
               'state':'draft',
               }

class location_master(osv.osv):
    _name = 'location.master'
    _order = "id desc"

    _columns ={
               'loc_id':fields.char('ID',size=64,readonly=True),
               'name':fields.char('Location Name',size=64),
               }
class maintenace_master(osv.osv):
    _name = 'maintenace.master'
    _order = "id desc"

    _columns ={
               'loc_id':fields.char('ID',size=64,readonly=True),
               'partner_id':fields.many2one('res.partner','Name'),
               'location_id':fields.many2one('stock.location','Location Name',size=64),
               'name':fields.char('Name',size=64,),
               'task_lines':fields.one2many('select.task','main_id','Tasks'),
               'feedback':fields.text('Feedback'),
               'state': fields.selection([('draft', 'New'),('process', 'Processing'), ('done', 'Done')], 'Status'),
               }
    _defaults={
               'state':'draft'
               
               }
    
    def create(self, cr, uid, vals, context=None):
         vals['loc_id'] = self.pool.get('ir.sequence').get(cr, uid, 'maintenace.master')
         return super(maintenace_master, self).create(cr, uid, vals, context=context)
    def onchange_partner(self,cr, uid, ids, partner_id):
        res={}
        if partner_id:
            res={
                 'state':'process'
                 }
        else:
            res={
                 'state':'draft'
                 }
        return {'value':res}
        
        
    def onchange_location(self, cr, uid, ids, location_id):
        res={}
        if location_id:
            obj=self.pool.get('stock.location').browse(cr, uid, location_id)
            res={
                 'name':obj.name
                 
                 }
        
        return {'value':res}
    
    
class task_master(osv.osv):
    _name = 'task.master'
    _order = "id desc"

    _columns ={
               'loc_id':fields.char('ID',size=64,readonly=True),
               'location_id':fields.many2one('stock.location','Location Name',size=64),
               'name':fields.char('Name',size=64,),
               'task_lines':fields.one2many('select.task','task_id','Tasks'),
               }
    def create(self, cr, uid, vals, context=None):
         vals['loc_id'] = self.pool.get('ir.sequence').get(cr, uid, 'task.master')
         return super(task_master, self).create(cr, uid, vals, context=context)
    def onchange_location(self, cr, uid, ids, location_id):
        res={}
        if location_id:
            obj=self.pool.get('stock.location').browse(cr, uid, location_id)
            res={
                 'name':obj.name
                 
                 }
        
        return {'value':res}
    
    _defaults={

               }

class select_task(osv.osv):
    _name='select.task'
    def _seq_no(self, cr, uid, ids, name, arg, context=None):
        res = {}
        count = 1
        for each in self.browse(cr, uid, ids):
            res[each.id] = 'Task'+' ' + str(count)
            count += 1
        return res
    _columns ={
               'main_id':fields.many2one('maintenace.master',),
               'task_id':fields.many2one('task.master',),
               'task_mgr_id':fields.many2one('task.manager',),
               'product':fields.many2one('product.product','Product'),
               'issue':fields.char('Issue',size=64),
               'priority':fields.selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], 'Priority',),
               'serial':fields.function( _seq_no , string='Sr.No.', type='char',size=10,method=True,),
               'name':fields.char('Description',size=64),
               'location_id':fields.many2one('stock.location','Location Name',size=64),
               'task':fields.boolean('Done'),
               }
    
class task_manager(osv.osv):
    _name = 'task.manager'
    _order = "id desc"

    _columns ={
               'loc_id':fields.char('ID',size=64,readonly=True),
               'emp_id':fields.many2one('hr.employee','Name'),
               'location':fields.many2one('task.master','Select Location'),
               'date':fields.datetime('Date'),
               'verify':fields.many2one('res.users','Verified By'),
               'task_lines':fields.one2many('select.task','task_mgr_id','Tasks'),
               'description':fields.text('Description/Remarks'),
               }
    def create(self, cr, uid, vals, context=None):
         vals['loc_id'] = self.pool.get('ir.sequence').get(cr, uid, 'task.manager')
         return super(task_manager, self).create(cr, uid, vals, context=context)
    def onchange_location(self, cr, uid, ids, location, context=None):
        res={}
        list=[]
        if location:
            obj=self.pool.get('task.master').browse(cr,uid,location)
            for val in obj.task_lines:
                list.append((0,0,{'serial':val.serial,'name':val.name}))
            
            res={
                 'task_lines':list
                 }
        return {'value':res}

    _defaults={
               'date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
               'verify':lambda obj, cr, uid, context: uid,
               }
    
class product_product(osv.osv):
    _description = "Product Details"
    _inherit = "product.product"
    
    def _get_id(self, cr,uid,c):
         res=0
         res=self.pool.get('product.category').search(cr,uid,[('name','ilike','Inter')])
         return res
     
    _columns = {
        'type': fields.selection([('consu', 'Consumable'), ('product', 'Stockable Product'), ('service', 'Service'), ('asset', 'Asset')], 'Product Type',),
        }
    _defaults={
               'type':'asset',
               'categ_id':lambda self,cr,uid,c: self._get_id(cr, uid, c),
               'sale_ok':False
               }
product_product()