import time
from openerp.osv import fields, osv
import datetime
from openerp import tools
from openerp.tools.translate import _
import email
import logging
import pytz
import re
import time
import xmlrpclib
from email.message import Message
from openerp.addons.mail.mail_message import decode

from datetime import timedelta
from dateutil import relativedelta
import calendar
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta as td

import time                            
from datetime import date
from datetime import timedelta
from dateutil import relativedelta
import calendar

from openerp import tools
from openerp import SUPERUSER_ID
from openerp.addons.mail.mail_message import decode
from openerp.osv import fields, osv, orm
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _




class res_users(osv.osv):
    _name = "res.users"
    
    _inherit = "res.users"
    _columns = {
                'notes':fields.text('List of Employees who have completed 1 year of Service'),
                }
    
    def send_one_year_mail(self, cr, uid, ids, context=None):  #### Scheduler for sending a mail to HR Officer mentioning the names of all those employees who have completed 1 year
         
         search_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','>',0)])
         
            
            
         
         
         list_of_emp = []
         
         for d in self.pool.get('hr.employee').browse(cr, uid, search_emp_record):
             emp_joining_date = d.joining_date
             work_status = d.work_status
             
             from time import strftime
             current_date = strftime("%Y-%m-%d")
            
             
             
            
             from datetime import datetime
             today_date = datetime.strptime(current_date,"%Y-%m-%d")
             emp_joining_date = datetime.strptime(d.joining_date,"%Y-%m-%d")
            
             months_difference = self.pool.get('hr.employee').diff_month(cr,uid,ids,today_date,emp_joining_date) 
            
             
             
             self.pool.get('hr.employee').write(cr, uid, d.id, {'no_of_months_worked':months_difference})
             
             
             
             if (months_difference == 12 and work_status == 'Temperory'):
                 
                    list_of_emp.append(d.name)
                    
          
         names_of_emp = list_of_emp
         
         search_group = self.pool.get('res.groups').search(cr,uid,[('name','=','Officer')])
         
         cr.execute("select uid from res_groups_users_rel where gid = %(val)s",{'val':search_group[0]})
         user_id = cr.fetchall()[1]
         
         
         
         search_user_id = self.pool.get('res.users').search(cr, uid, [('id','=',user_id)])
         

         for i in self.pool.get('res.users').browse(cr,uid,search_user_id):
             self.pool.get('res.users').write(cr,uid,i.id,{'notes':names_of_emp})
             
         email_template_obj = self.pool.get('email.template')
                                                 
         template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','res.users'),('model_object_field.name', '=','user_email')], context=context)
         
        
         if template_ids:                                  
            mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], search_user_id[0], force_send=True, context=context)


         return True



class hr_holidays_status(osv.osv):
    _name = "hr.holidays.status"
    _description = "Leave Types"
    _inherit = "hr.holidays.status"
    _columns = {
                'is_leave_allowance':fields.boolean('Leave Allowance Allowed', size=64),
                }


class attendance_batch(osv.osv):
    _name = "attendance.batch"
    _description = "Attendance Batch"
    _columns = {
                'name': fields.char('Batch Name', size=64, required=True),
                'date_from': fields.date('Date From', size=64, required=True),
                'date_to': fields.date('Date To', size=64, required=True),
                'state': fields.selection([
                                           ('draft', 'Draft'),
                                           ('done', 'Done'),
                                           ], 'Status', select=True, readonly=True),
                'attendance_batch_line': fields.one2many('hr.attendance.table', 'batch_attendance_id', 'Batch Attendance Slips', size=64),
                }
    _defaults = {
        'state': 'draft',
        
    }
    
    def generate_batch(self,cr,uid,ids,context=None):
        
        return {
            'name':"Batch Generation of Monthly Attendance Slips",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.batch.attendance.slips',
            'res_id': '',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            #'context': default_context,
         }
        
    
attendance_batch()

class mail_thread(osv.osv):
    _name = "mail.thread"
    _description = "Mails"
    _inherit = "mail.thread"
    
    _columns={
            
            }

#     def message_parse(self, cr, uid, message, save_original=False, context=None):
#         msg_dict = {
#                     'type': 'email',
#                     'author_id': False,
#                 }
#         if not isinstance(message, Message):
#            if isinstance(message, unicode):
#                         
#               message = message.encode('utf-8')
#            message = email.message_from_string(message)
#         
#         message_id = message['message-id']
#         if not message_id:
#                     
#            message_id = "<%s@localhost>" % time.time()
#            import logging
#            # _logger.debug('Parsing Message without message-id, generating a random one: %s', message_id)
#         msg_dict['message_id'] = message_id
#         
#         if message.get('Subject'):
#            msg_dict['subject'] = decode(message.get('Subject'))
#         
#                 
#         msg_dict['from'] = decode(message.get('from'))
#         msg_dict['to'] = decode(message.get('to'))
#         msg_dict['cc'] = decode(message.get('cc'))
#         
#         if message.get('From'):
#            author_ids = self._message_find_partners(cr, uid, message, ['From'], context=context)
#            if author_ids:
#               msg_dict['author_id'] = author_ids[0]
#            msg_dict['email_from'] = decode(message.get('from'))
#         partner_ids = self._message_find_partners(cr, uid, message, ['To', 'Cc'], context=context)
#         msg_dict['partner_ids'] = [(4, partner_id) for partner_id in partner_ids]
#         
#         if message.get('Date'):
#            try:
#               date_hdr = decode(message.get('Date'))
#               parsed_date = dateutil.parser.parse(date_hdr, fuzzy=True)
#               if parsed_date.utcoffset() is None:
#                             
#                  stored_date = parsed_date.replace(tzinfo=pytz.utc)
#               else:
#                  stored_date = parsed_date.astimezone(tz=pytz.utc)
#            except Exception:
#                  import logging
#                  #_logger.warning('Failed to parse Date header %r in incoming mail '
#                  #                       'with message-id %r, assuming current date/time.',
#                  #                       message.get('Date'), message_id)
#                  stored_date = datetime.datetime.now()
#            msg_dict['date'] = stored_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
#         
#         if message.get('In-Reply-To'):
#            parent_ids = self.pool.get('mail.message').search(cr, uid, [('message_id', '=', decode(message['In-Reply-To']))])
#            if parent_ids:
#               msg_dict['parent_id'] = parent_ids[0]
#         
#         if message.get('References') and 'parent_id' not in msg_dict:
#            parent_ids = self.pool.get('mail.message').search(cr, uid, [('message_id', 'in',
#                                                                                  [x.strip() for x in decode(message['References']).split()])])
#            if parent_ids:
#               msg_dict['parent_id'] = parent_ids[0]
#         
#         print msg_dict['subject'], "----------------------------------THIS IS SUBJECT OF THE MAIL-------------------------------------"
#         msg_dict['body'], msg_dict['attachments'] = self._message_extract_payload(cr, uid, message, save_original=save_original)
#         return msg_dict
    
    def message_process(self, cr, uid, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None, context=None):
        """ Process an incoming RFC2822 email message, relying on
            ``mail.message.parse()`` for the parsing operation,
            and ``message_route()`` to figure out the target model.

            Once the target model is known, its ``message_new`` method
            is called with the new message (if the thread record did not exist)
            or its ``message_update`` method (if it did).

            There is a special case where the target model is False: a reply
            to a private message. In this case, we skip the message_new /
            message_update step, to just post a new message using mail_thread
            message_post.

           :param string model: the fallback model to use if the message
               does not match any of the currently configured mail aliases
               (may be None if a matching alias is supposed to be present)
           :param message: source of the RFC2822 message
           :type message: string or xmlrpclib.Binary
           :type dict custom_values: optional dictionary of field values
                to pass to ``message_new`` if a new record needs to be created.
                Ignored if the thread record already exists, and also if a
                matching mail.alias was found (aliases define their own defaults)
           :param bool save_original: whether to keep a copy of the original
                email source attached to the message after it is imported.
           :param bool strip_attachments: whether to strip all attachments
                before processing the message, in order to save some space.
           :param int thread_id: optional ID of the record/thread from ``model``
               to which this mail should be attached. When provided, this
               overrides the automatic detection based on the message
               headers.
        """
        if context is None:
            context = {}

        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = str(message.data)
        # Warning: message_from_string doesn't always work correctly on unicode,
        # we must use utf-8 strings here :-(
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        msg_txt = email.message_from_string(message)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg = self.message_parse(cr, uid, msg_txt, save_original=save_original, context=context)
        if strip_attachments:
            msg.pop('attachments', None)
        if msg.get('message_id'):   # should always be True as message_parse generate one if missing
            existing_msg_ids = self.pool.get('mail.message').search(cr, SUPERUSER_ID, [
                                                                ('message_id', '=', msg.get('message_id')),
                                                                ], context=context)
            if existing_msg_ids:
               # _logger.info('Ignored mail from %s to %s with Message-Id %s:: found duplicated Message-Id during processing',
               #                 msg.get('from'), msg.get('to'), msg.get('message_id'))
                return False

        # find possible routes for the message
        routes = self.message_route(cr, uid, msg_txt, model,
                                    thread_id, custom_values,
                                    context=context)

        # postpone setting msg.partner_ids after message_post, to avoid double notifications
        partner_ids = msg.pop('partner_ids', [])

        thread_id = False
        for model, thread_id, custom_values, user_id in routes:
            if self._name == 'mail.thread':
                context.update({'thread_model': model})
            if model:
                model_pool = self.pool.get(model)
                assert thread_id and hasattr(model_pool, 'message_update') or hasattr(model_pool, 'message_new'), \
                    "Undeliverable mail with Message-Id %s, model %s does not accept incoming emails" % \
                        (msg['message_id'], model)

                # disabled subscriptions during message_new/update to avoid having the system user running the
                # email gateway become a follower of all inbound messages
                nosub_ctx = dict(context, mail_create_nosubscribe=True)
                if thread_id and hasattr(model_pool, 'message_update'):
                    model_pool.message_update(cr, user_id, [thread_id], msg, context=nosub_ctx)
                else:
                    nosub_ctx = dict(nosub_ctx, mail_create_nolog=True)
                    thread_id = model_pool.message_new(cr, user_id, msg, custom_values, context=nosub_ctx)
            else:
                assert thread_id == 0, "Posting a message without model should be with a null res_id, to create a private message."
                model_pool = self.pool.get('mail.thread')
            new_msg_id = model_pool.message_post(cr, uid, [thread_id], context=context, subtype='mail.mt_comment', **msg)

            if partner_ids:
                # postponed after message_post, because this is an external message and we don't want to create
                # duplicate emails due to notifications
                self.pool.get('mail.message').write(cr, uid, [new_msg_id], {'partner_ids': partner_ids}, context=context)

        return thread_id

    def message_new(self, cr, uid, msg_dict, custom_values=None, context=None):
        """Called by ``message_process`` when a new message is received
           for a given thread model, if the message did not belong to
           an existing thread.
           The default behavior is to create a new record of the corresponding
           model (based on some very basic info extracted from the message).
           Additional behavior may be implemented by overriding this method.

           :param dict msg_dict: a map containing the email details and
                                 attachments. See ``message_process`` and
                                ``mail.message.parse`` for details.
           :param dict custom_values: optional dictionary of additional
                                      field values to pass to create()
                                      when creating the new thread record.
                                      Be careful, these values may override
                                      any other values coming from the message.
           :param dict context: if a ``thread_model`` value is present
                                in the context, its value will be used
                                to determine the model of the record
                                to create (instead of the current model).
           :rtype: int
           :return: the id of the newly created thread object
        """
        
        print msg_dict, "***************************** NEW MESSAGE ARRIVED *******************************************"
        
        if context is None:
            context = {}
        data = {}
        if isinstance(custom_values, dict):
            data = custom_values.copy()
        model = context.get('thread_model') or self._name
        model_pool = self.pool.get(model)
        fields = model_pool.fields_get(cr, uid, context=context)
        if 'name' in fields and not data.get('name'):
            data['name'] = msg_dict.get('subject', '')
        res_id = model_pool.create(cr, uid, data, context=context)
        return res_id

    def message_update(self, cr, uid, ids, msg_dict, update_vals=None, context=None):
        """Called by ``message_process`` when a new message is received
           for an existing thread. The default behavior is to update the record
           with update_vals taken from the incoming email.
           Additional behavior may be implemented by overriding this
           method.
           :param dict msg_dict: a map containing the email details and
                               attachments. See ``message_process`` and
                               ``mail.message.parse()`` for details.
           :param dict update_vals: a dict containing values to update records
                              given their ids; if the dict is None or is
                              void, no write operation is performed.
        """
        if update_vals:
            self.write(cr, uid, ids, update_vals, context=context)
        return True

 
     
#     def _message_extract_payload(self, cr, uid, message, save_original=False):
#         """Extract body as HTML and attachments from the mail message"""
#         
#         print "tttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt"
#         
#         attachments = []
#         body = u''
#         
#         if save_original:
#             
#             attachments.append(('original_email.eml', message.as_string()))
#         if not message.is_multipart() or 'text/' in message.get('content-type', ''):
#             encoding = message.get_content_charset()
#             body = message.get_payload(decode=True)
#             body = tools.ustr(body, encoding, errors='replace')
#             if message.get_content_type() == 'text/plain':
#                 
#                 body = tools.append_content_to_html(u'', body, preserve=True)
#         else:
#             
#             
#             alternative = (message.get_content_type() == 'multipart/alternative')
#             for part in message.walk():
#                 
#                 if part.get_content_maintype() == 'multipart':
#                     continue  
#                 filename = part.get_filename()  
#                 
#                 encoding = part.get_content_charset()  
#                 
#                 if filename or part.get('content-disposition', '').strip().startswith('attachment'):
#                     
#                     attachments.append((filename or 'attachment', part.get_payload(decode=True)))
#                     
#                     #self.import_attendance(cr,uid,part.get_payload())
#                     
#                     continue
#                 
#                 if part.get_content_type() == 'text/plain' and (not alternative or not body):
#                     body = tools.append_content_to_html(body, tools.ustr(part.get_payload(decode=True),
#                                                                          encoding, errors='replace'), preserve=True)
#                 
#                 elif part.get_content_type() == 'text/html':
#                     html = tools.ustr(part.get_payload(decode=True), encoding, errors='replace')
#                     if alternative:
#                         body = html
#                     else:
#                         body = tools.append_content_to_html(body, html, plaintext=False)
#                 
#                 else:
#                     
#                     
#                     attachments.append((filename or 'attachment', part.get_payload(decode=True)))
#         
#         #print body, "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu"
#         return body, attachments




mail_thread()


class hr_employee(osv.osv):
    _name = "hr.employee"
    _description = "HR Employee"
    _inherit = "hr.employee"
    
    def _set_remaining_days(self, cr, uid, empl_id, name, value, arg, context=None):
        employee = self.browse(cr, uid, empl_id, context=context)
        diff = value - employee.remaining_leaves
        type_obj = self.pool.get('hr.holidays.status')
        holiday_obj = self.pool.get('hr.holidays')
        # Find for holidays status
        status_ids = type_obj.search(cr, uid, [('limit', '=', False)], context=context)
        if len(status_ids) != 1 :
             raise osv.except_osv(_('Warning!'),_("The feature behind the field 'Remaining Legal Leaves' can only be used when there is only one leave type with the option 'Allow to Override Limit' unchecked. (%s Found). Otherwise, the update is ambiguous as we cannot decide on which leave type the update has to be done. \nYou may prefer to use the classic menus 'Leave Requests' and 'Allocation Requests' located in 'Human Resources \ Leaves' to manage the leave days of the employees if the configuration does not allow to use this field.") % (len(status_ids)))
        status_id = status_ids and status_ids[0] or False
        if not status_id:
            return False
        if diff > 0:
            leave_id = holiday_obj.create(cr, uid, {'name': _('Allocation for %s') % employee.name, 'employee_id': employee.id, 'holiday_status_id': status_id, 'type': 'add', 'holiday_type': 'employee', 'number_of_days_temp': diff}, context=context)
        elif diff < 0:
            leave_id = holiday_obj.create(cr, uid, {'name': _('Leave Request for %s') % employee.name, 'employee_id': employee.id, 'holiday_status_id': status_id, 'type': 'remove', 'holiday_type': 'employee', 'number_of_days_temp': abs(diff)}, context=context)
        else:
            return False
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'hr.holidays', leave_id, 'confirm', cr)
        wf_service.trg_validate(uid, 'hr.holidays', leave_id, 'validate', cr)
        wf_service.trg_validate(uid, 'hr.holidays', leave_id, 'second_validate', cr)
        return True

    def _get_remaining_days(self, cr, uid, ids, name, args, context=None):
        cr.execute("""SELECT
                sum(h.number_of_days) as days,
                h.employee_id
            from
                hr_holidays h
                join hr_holidays_status s on (s.id=h.holiday_status_id)
            where
                h.state='validate' and
                s.limit=False and
                h.employee_id in (%s)
            group by h.employee_id"""% (','.join(map(str,ids)),) )
        res = cr.dictfetchall()
        remaining = {}
        for r in res:
            remaining[r['employee_id']] = r['days']
        for employee_id in ids:
            if not remaining.get(employee_id):
                remaining[employee_id] = 0.0
        return remaining
    
    def _get_number_of_children(self,cr,uid,ids,fields,args,context):
       res={}
       for val in self.browse(cr,uid,ids):
           
           search_no_of_children = self.pool.get('children.details').search(cr, uid, [('child_id','=',ids[0]),('id','>',0)])
           
           res[val.id] = len(search_no_of_children)
       return res
    
    _columns = {
        'attendance': fields.boolean('Attendance', size=124),
        'children_line':fields.one2many('children.details','child_id'," ", size=124),
        'carry_forwarded_leaves':fields.float('Carry Forwaded Leaves From Previous Year Leave Cycle (in days)', size=64),
        'joining_date':fields.date('Joining Date', size=64, required=True),
        'no_of_children': fields.function(_get_number_of_children,type='integer',string='Number of Children'),
        'no_of_months_worked':fields.integer('Number of months worked', size=64),
        'work_status': fields.selection([('Temperory','Temperory'),('Permanent','Permanent')], 'Work Status'),
        'department_name':fields.char('Department Name', size=64),
        }
    
    def onchange_department_id(self, cr, uid, ids, department_id):
            v={}
            if department_id:
               partner1=self.pool.get('hr.department').browse(cr, uid, department_id)
               v['department_name']=partner1.name
               v['department_id']=partner1.id
            
            
            return {'value':v}
    
    def diff_month(self,cr,uid,ids,d1,d2):
        return (d1.year - d2.year)*12 + d1.month - d2.month
    
    
    
        
    def create(self, cr, uid, vals, context=None):
        new_id = []
        # don't pass the value of remaining leave if it's 0 at the creation time, otherwise it will trigger the inverse
        # function _set_remaining_days and the system may not be configured for. Note that we don't have this problem on
        # the write because the clients only send the fields that have been modified.
        if 'remaining_leaves' in vals and not vals['remaining_leaves']:
            del(vals['remaining_leaves'])
            
        new_id = super(hr_employee, self).create(cr, uid, vals, context=context)
         
        allocate_ids = self.pool.get('hr.holidays').create(cr, uid, {'type':'add', 'employee_id':new_id, 'holiday_type':'employee', 'holiday_status_id':1, 'number_of_days_temp':0, 'state':'validate'})
        self.pool.get('hr.holidays').holidays_validate(cr, uid, [allocate_ids], context=None)
        
            
class children_details(osv.osv):
    _name = "children.details"
    _description = "Children Details"
    _columns = {
        'child_id': fields.many2one('hr.employee','Children Details', size=64),
        'child_no': fields.integer('Child No.', size=64),
        'dob':fields.date('Date of Birth', size=64, required=True),
        'age':fields.integer('Age', size=64),
        

        }
    
    def onchange_dob(self,cr,uid,ids,dob):
        if dob:
            
            
            from time import strftime
            
            
            dob_year = int(dob[:4])
            
            dob_month = int(dob[5:7])
            
            dob_date = int(dob[8:10])
            
            
            
            
            today_date = strftime("%Y-%m-%d")
                
            current_year=int(today_date[:4])
            
                
            current_month=int(today_date[5:7])
            
                
            current_date=int(today_date[8:10])
            
            
            from dateutil.relativedelta import relativedelta
            date1 = date(dob_year,dob_month,dob_date)
            date2 = date(current_year,current_month,current_date)
            
            difference_in_years = relativedelta(date2, date1).years
            
            
            return {'value' : {'age':difference_in_years}}
        return {'value' : {'age':False}}

children_details()

    


class hr_holidays(osv.osv):
    _name = "hr.holidays"
    _description = "HR Holidays"
    _inherit = "hr.holidays"
    _columns = {
        'serial_no': fields.char('Serial No.', size=124),
        'category': fields.many2one('hr.employee.category',"Employee Category", size=124),
        'attachment_line':fields.one2many('ir.attachment','attachment_id','Attachments', size=124),
        'onchange_holiday_status_id':fields.char('On Change holiday status', size=100),
        'is_apply_leave_allowance':fields.boolean('Apply Leave Allowance', size=64),
        'virtual_is_leave_allowance':fields.boolean('Leave Allowance allowed', size=64),
        }
    
    def onchange_holiday_status_id(self, cr, uid, ids, holiday_status_id):
            v={}
            if holiday_status_id:
               partner1=self.pool.get('hr.holidays.status').browse(cr, uid, holiday_status_id)
               v['onchange_holiday_status_id']=partner1.name
               v['holiday_status_id']=partner1.id
            holiday_status_obj=self.pool.get('hr.holidays.status')
            obj=self.browse(cr, uid, ids)
            holidays_status_ids = holiday_status_obj.search(cr, uid, [('id','=',holiday_status_id)])
            line = holiday_status_obj.browse(cr,uid,holidays_status_ids[0])
            if line.is_leave_allowance == True:
                v = {
                       'virtual_is_leave_allowance':True,
                       }
            else:
                v = {
                       'virtual_is_leave_allowance':False,
                       }
            
            
            return {'value':v}
        
    
    def holidays_first_validate(self, cr, uid, ids, context=None):
        
        self.check_holidays(cr, uid, ids, context=context)
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        self.holidays_first_validate_notificate(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'state':'validate1', 'manager_id': manager})
    
    def holidays_validate(self, cr, uid, ids, context=None):
        
        
        
        for d in self.browse(cr, uid, ids, context=None):
            
            employee_id=d.employee_id.id
            user_id=d.employee_id.user_id.id
            if d.date_from == False:
                d.date_from = '2013-01-01 00:00:00'
            if d.date_to == False:
                d.date_to = '2013-01-01 00:00:00'
            date_from=d.date_from[:10]
            
            date_to=d.date_to[:10]
            
            list=[]
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            from_dt = datetime.datetime.strptime(d.date_from, DATETIME_FORMAT).date()
            
            to_dt = datetime.datetime.strptime(d.date_to, DATETIME_FORMAT).date()
            
            
            delta= to_dt - from_dt
            for i in range(delta.days + 1):
                list.append(str(from_dt + td(days=i)))
                
         ### End of Code for ISA       
            
        self.check_holidays(cr, uid, ids, context=context)
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        self.write(cr, uid, ids, {'state':'validate'})
        data_holiday = self.browse(cr, uid, ids)
        for record in data_holiday:
            if record.double_validation:
                self.write(cr, uid, [record.id], {'manager_id2': manager})
            else:
                self.write(cr, uid, [record.id], {'manager_id': manager})
            if record.holiday_type == 'employee' and record.type == 'remove':
                meeting_obj = self.pool.get('crm.meeting')
                meeting_vals = {
                    'name': record.name or _('Leave Request'),
                    'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
                    'duration': record.number_of_days_temp * 8,
                    'description': record.notes,
                    'user_id': record.user_id.id,
                    'date': record.date_from,
                    'end_date': record.date_to,
                    'date_deadline': record.date_to,
                    'state': 'open',            # to block that meeting date in the calendar
                }
                meeting_id = meeting_obj.create(cr, uid, meeting_vals)
                self._create_resource_leave(cr, uid, [record], context=context)
                self.write(cr, uid, ids, {'meeting_id': meeting_id})
            elif record.holiday_type == 'category':
                emp_ids = obj_emp.search(cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
                leave_ids = []
                for emp in obj_emp.browse(cr, uid, emp_ids):
                    vals = {
                        'name': record.name,
                        'type': record.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': record.holiday_status_id.id,
                        'date_from': record.date_from,
                        'date_to': record.date_to,
                        'notes': record.notes,
                        'number_of_days_temp': record.number_of_days_temp,
                        'parent_id': record.id,
                        'employee_id': emp.id
                    }
                    leave_ids.append(self.create(cr, uid, vals, context=None))
                wf_service = netsvc.LocalService("workflow")
                for leave_id in leave_ids:
                    wf_service.trg_validate(uid, 'hr.holidays', leave_id, 'confirm', cr)
                    wf_service.trg_validate(uid, 'hr.holidays', leave_id, 'validate', cr)
                    wf_service.trg_validate(uid, 'hr.holidays', leave_id, 'second_validate', cr)
        
        ### Code for ISA
        
        attendance_search=self.pool.get('hr.attendance.table.line').search(cr,uid, [('employee_id','=',employee_id),('date', 'in', list),('final_result','=','A')])
        
        for val in attendance_search:
            self.pool.get('hr.attendance.table.line').write(cr, uid, val, {'absent_info':'PL','final_result':'PL'})
        
        ### End of Code for ISA
                
        return True
    
    def last_day_of_month(self,cr,uid,ids,year, month):
        from datetime import datetime
        """ Work out the last day of the month """
        last_days = [31, 30, 29, 28, 27]
        
        for i in last_days:
                try:
                    end = datetime(year, month, i)
                    
                        
                except ValueError:
                        continue
                else:
                    return end.date()
        return None
    
    def holidays_confirm(self, cr, uid, ids, context=None):
        self.check_holidays(cr, uid, ids, context=context)
        for record in self.browse(cr, uid, ids, context=context):
            form_id = record.id
            employee_id = record.employee_id.id
            holiday_status_id = record.holiday_status_id.name
            no_of_days = record.number_of_days_temp
            
            search_doc_cert = self.pool.get('ir.attachment').search(cr, uid, [('attachment_id','=',form_id)])
            
            if (holiday_status_id == 'Sick Leaves' and not search_doc_cert):
                raise osv.except_osv(_('Error!'), _("You cannot apply for a Sick Leave unless you attach a Doctor's Certificate"))
            
            if (holiday_status_id == 'Marriage Leave' and no_of_days >10):
                raise osv.except_osv(_('Error!'), _("You cannot apply for a Marriage Leave more than 10 days"))
            
            search_employee = self.pool.get('hr.employee').search(cr, uid, [('id','=',employee_id)])
            
            for h in self.pool.get('hr.employee').browse(cr, uid, search_employee):
                emp_gender = h.gender
                marital_status = h.marital
                children = h.children
                
                
                if (holiday_status_id == 'Maternity Leave' and emp_gender == 'male'):
                    raise osv.except_osv(_('Error!'), _("You cannot apply for a Maternity Leave"))
                if (holiday_status_id == 'Maternity Leave' and marital_status == 'single'):
                    raise osv.except_osv(_('Error!'), _("Since you are single, you cannot apply for a Maternity Leave"))
                
            
            if record.date_from == False:
                record.date_from = '2013-01-01 00:00:00'
                
            if record.date_to == False:
                record.date_to = '2013-01-01 00:00:00'
                
                
            
            date_from = record.date_from[:10]
            date_to = record.date_to[:10]
            
            DATETIME_FORMAT = "%Y-%m-%d"
            from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT).date()
            
            
            date_from_year = int(record.date_from[:4])
            date_from_month = int(record.date_from[5:7])
            date_from_date = int(record.date_from[8:10])
            
            from dateutil.relativedelta import relativedelta
            date_after_3months = date(date_from_year,date_from_month,date_from_date) + relativedelta(months = +3)
            date_after_4months = date(date_from_year,date_from_month,date_from_date) + relativedelta(months = +4)
            
            
            if (holiday_status_id == 'Maternity Leave' and children == 0 and date_to > str(date_after_3months)):
                    raise osv.except_osv(_('Error!'), _("You can apply for a Maternity Leave for 3 months only"))
            
            if (holiday_status_id == 'Maternity Leave' and (children >= 1 and children <= 3) and date_to > str(date_after_4months)):
                    raise osv.except_osv(_('Error!'), _("You can apply for a Maternity Leave for 4 months only"))
                
            if (holiday_status_id == 'Maternity Leave' and children >3):
                    raise osv.except_osv(_('Error!'), _("You cannot apply for a Maternity Leave"))
            
            search_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','=',employee_id)])
            
            
            
            for c in self.pool.get('hr.employee').browse(cr,uid,search_emp_record):
                
          #----------------- Current Date -------------------------------------      
                from time import strftime
                today_date = strftime("%Y-%m-%d")
                
                current_year=int(today_date[:4])
                
                current_month=int(today_date[5:7])
                
                current_date=int(today_date[8:10])
          #-----------------End of Current Date -------------------------------------  
          
          
          
          #-----------------Date before 1 month-------------------------------------    
                from dateutil.relativedelta import relativedelta
                date_before_1month = date(current_year,current_month,current_date) + relativedelta(months = -1)
                
                DATETIME_FORMAT = "%Y-%m-%d"
                dt_before_1month = str(date_before_1month)
                
                date_before_1month_year=int(dt_before_1month[:4])
                
                date_before_1month_month=int(dt_before_1month[5:7])
                
                date_before_1month_date=int(dt_before_1month[8:10])
                
           #-----------------End of Date before 1 month-------------------------------------     
           
           #-----------------Start Date and End Date of previous Month-------------------------
                start_date = date(date_before_1month_year,date_before_1month_month,1)
                
                last_date = self.last_day_of_month(cr,uid,ids,date_before_1month_year,date_before_1month_month)
                
                
                
           #-----------------End of Start Date and End Date of previous Month-------------------------
                
           
           
           #-----------------Date of Joining-------------------------------------
                
                date_of_joining = c.joining_date
                dt_of_joining = datetime.datetime.strptime(date_of_joining, DATETIME_FORMAT).date()
                
                emp_joining_year=int(c.joining_date[:4])
                emp_joining_month=int(c.joining_date[5:7])
                emp_joining_date=int(c.joining_date[8:10])
                from dateutil.relativedelta import relativedelta
                doj_format = date(emp_joining_year,emp_joining_month,emp_joining_date)
                
                
            #-----------------End of Date of Joining-------------------------------------  
                
                if doj_format not in (start_date,last_date):
                    
                    search_doj = self.pool.get('hr.holidays').search(cr, uid, [('type','=','add')])
                    

            #-----------------Date after 6 months-------------------------------------    
                date_after_6months = date(emp_joining_year,emp_joining_month,emp_joining_date) + relativedelta(months=+6)
            #-----------------End of Date after 6 months-------------------------------------   
#                 
            if (date_from>=str(doj_format) and date_from<=str(date_after_6months)):
                raise osv.except_osv(_('Warning!'),_("You cannot apply for a leave in your probationary period"))
                
                
            if record.employee_id and record.employee_id.parent_id and record.employee_id.parent_id.user_id:
                self.message_subscribe_users(cr, uid, [record.id], user_ids=[record.employee_id.parent_id.user_id.id], context=context)
        return self.write(cr, uid, ids, {'state': 'confirm'})
    

    
hr_holidays()

class ir_attachment(osv.osv):
    _name = "ir.attachment"
    _description = "Attachments"
    _inherit = "ir.attachment"
    _columns = {
        'attachment_id': fields.many2one('hr.holidays','Attachments', size=124),
        }

ir_attachment()



class hr_payslip_line(osv.osv):
    _name = "hr.payslip.line"
    _description = "Payslip Line"
    _inherit = "hr.payslip.line"
    
    def _calculate_total(self, cr, uid, ids, name, args, context):
        if not ids: return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
           # res[line.id] = float(line.quantity) * line.amount * line.rate / 100
           x = float(line.quantity) * line.amount * line.rate / 100
           res[line.id] = x
        return res
    
    _columns = {
                'total': fields.function(_calculate_total, method=True, type='float', string='Total', digits_compute=dp.get_precision('Payroll'),store=True ),
                }

class irt_table(osv.osv):
    _name = "irt.table"
    _description = "IRT Table"
    _columns = {
        'name':fields.char('IRT Table', size=64),
        'irt_line':fields.one2many('irt.table.line','irt_id',size=124),
        }

irt_table()

class irt_table_line(osv.osv):
    _name = "irt.table.line"
    _description = "IRT Table Lines"
    _columns = {
        'irt_id':fields.many2one('irt.table','IRT ID', size=64),
        'a_from_value':fields.integer('A (FROM)', size=64),
        'a_to_value':fields.integer('A (TO)', size=64),
        'b_value':fields.integer('B', size=64),
        'c_value':fields.float('C', size=64),
        'd_value':fields.float('D (in $)', size=64),
        'e_value':fields.float('E', size=64),
        'f_value':fields.float('F', size=64),
        'g_value':fields.float('G', size=64),
        'h_value':fields.float('H', size=64),
        }

irt_table_line()


class leaves_calendar(osv.osv):
    _name = "leaves.calendar"
    _description = "Public Holidays"
    _columns = {
        'holiday_id':fields.many2one('holidays.calendar','Holidays Number', size=124),        
        'name': fields.char('Holiday Name', size=124, required=True),
        'date_from': fields.date('Date', size=124),
        'day': fields.selection([('0','Monday'),('1','Tuesday'),('2','Wednesday'),('3','Thursday'),('4','Friday'),('5','Saturday'),('6','Sunday')], 'Day of Week'),
        'description': fields.text('Description', size=124),
        'type':fields.selection([('even_sat', 'Even Saturday')],'Type'),
        
        }
    
    def last_day_of_month(self,cr,uid,ids,year, month):
        from datetime import datetime
        """ Work out the last day of the month """
        last_days = [31, 30, 29, 28, 27]
        
        for i in last_days:
                try:
                    end = datetime(year, month, i)
                    
                        
                except ValueError:
                        continue
                else:
                    return end.date()
        return None
    
    def leave_cycle_for_december(self,cr,uid,ids,context=None):    #### Scheduler for Allocation and Carry-Forwarding of Leaves in December
        
        
        search_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','>',0)])
            
            
        for s in self.pool.get('hr.employee').browse(cr,uid,search_emp_record):
            # On 31st Dec
            remaining_leaves = s.remaining_leaves
            
            
            
            
            search_allocated_leaves = self.pool.get('hr.holidays').search(cr, uid, [('employee_id','=',s.id),('type','=','add')])
            
            for e in self.pool.get('hr.holidays').browse(cr, uid, search_allocated_leaves):
                number_of_allocated_days = e.number_of_days
                
                
                
                
                
            leaves_consumed = (number_of_allocated_days - remaining_leaves)
            
            
            
            
            from time import strftime
            today_date = strftime("%Y-%m-%d %H:%M:%S")
            
            #today_date = strftime("%Y-%m-%d")
            
            current_year=int(today_date[:4])
        
            
            current_month=int(today_date[5:7])
        
            
            current_date=int(today_date[8:10])
            
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            date_after_2days = datetime(current_year,current_month,current_date) + relativedelta(days = +2)
            
            
            
            remaining_leaves_by_end_of_Dec = (number_of_allocated_days - 10)
            
            
            
            search_carryforward_leave_type = self.pool.get('hr.holidays.status').search(cr, uid, [('name','=','Carried Forward Leaves')])
                
            for o in self.pool.get('hr.holidays.status').browse(cr, uid, search_carryforward_leave_type):
                    carry_forward_leave_type = o.id
            
            
            if (s.remaining_leaves > remaining_leaves_by_end_of_Dec) :
                
                
                carry_forward = self.pool.get('hr.holidays').create(cr, uid, {'employee_id':s.id, 'holiday_type':'employee', 'holiday_status_id':carry_forward_leave_type, 'type':'remove', 'number_of_days_temp': remaining_leaves_by_end_of_Dec, 'date_from' : date_after_2days, 'date_to' : date_after_2days})
                
                
            else:
                
                create_carry_forward = self.pool.get('hr.holidays').create(cr, uid, {'employee_id':s.id, 'holiday_type':'employee', 'holiday_status_id':carry_forward_leave_type, 'type':'remove', 'number_of_days_temp': s.remaining_leaves, 'date_from' : date_after_2days, 'date_to' : date_after_2days})
                
            
            ####### Logic by Ankit Sir
           # if remaining_leaves > 14:
            #    print "ttttttttttttttttttttttttttt"
                #create CARRIED FORWARD LEAVES = 14
            #else:
            #    print "kkkkkkkkkkkkkkkkkkkkkkkkkk"
                #create CARRIED FORWARD LEAVES = remaining_leaves
            
            #apply and approve legal leaves = remaining_leaves. Description: "Reset"
            ######## end of Logic by Ankit Sir
            if leaves_consumed < 10:
                leaves_to_be_deducted = (10 - leaves_consumed)
                
                
                search_legal_leave_type = self.pool.get('hr.holidays.status').search(cr, uid, [('name','=','Legal Leaves 2013')])
                
                for l in self.pool.get('hr.holidays.status').browse(cr, uid, search_legal_leave_type):
                    legal_leave_type = l.id
                leave_id = self.pool.get('hr.holidays').create(cr, uid, {'employee_id':s.id, 'holiday_type':'employee', 'holiday_status_id':legal_leave_type, 'type':'remove', 'number_of_days_temp': leaves_to_be_deducted, 'date_from' : today_date, 'date_to' : today_date})
                
                self.pool.get('hr.holidays').holidays_validate(cr, uid, [leave_id], context=None)
                
                
            
           
            
        return True

    
    def leave_cycle_for_march(self,cr,uid,ids,context=None):    #### Scheduler for Allocation of Leaves in March
        
        
        search_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','>',0)])
        
        
        for f in self.pool.get('hr.employee').browse(cr,uid,search_emp_record):
            # On 31st March
            remaining_leaves = f.remaining_leaves
            employee_id = f.id
            
        search_carryforward_leave_type = self.pool.get('hr.holidays.status').search(cr, uid, [('name','=','Carried Forward Leaves')])
                
        for o in self.pool.get('hr.holidays.status').browse(cr, uid, search_carryforward_leave_type):
                    carry_forward_leave_type = o.id
                    
            
        search_carry_forward_record = self.pool.get('hr.holidays').search(cr ,uid, [('type','=','remove'),('employee_id','=',employee_id),('holiday_status_id','=',carry_forward_leave_type)])    
        for d in self.pool.get('hr.holidays').browse(cr, uid, search_carry_forward_record):
            date_from = d.date_from
            
            
            carry_forward_year=int(date_from[:4])
             
            
            from time import strftime
            today_date = strftime("%Y-%m-%d %H:%M:%S")
            
            
            
            current_year=int(today_date[:4])
            
        
            if (carry_forward_year == current_year) :
                
                cr.execute("update hr_holidays set number_of_days_temp = 0 where employee_id = %(val1)s and type = 'remove' and holiday_status_id = %(val2)s and date_from = %(val3)s",{'val1':f.id, 'val2':carry_forward_leave_type, 'val3':date_from})
                cr.execute("update hr_holidays set number_of_days = number_of_days_temp where employee_id = %(val1)s and type = 'remove' and holiday_status_id = %(val2)s and date_from = %(val3)s",{'val1':f.id, 'val2':carry_forward_leave_type, 'val3':date_from})
        return True
    
    
    
    def allocate_monthly_two_leaves(self,cr,uid,ids,context=None):    #### Scheduler for Allocation of 2 Leaves per month
            
            search_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','>',0)])
            
            
            
            for c in self.pool.get('hr.employee').browse(cr,uid,search_emp_record):
                
          #----------------- Current Date -------------------------------------      
                from time import strftime
                today_date = strftime("%Y-%m-%d")
                
                current_year=int(today_date[:4])
                
                current_month=int(today_date[5:7])
                
                current_date=int(today_date[8:10])
          #-----------------End of Current Date -------------------------------------  
          
          
          
          #-----------------Date before 1 month-------------------------------------    
                from dateutil.relativedelta import relativedelta
                date_before_1month = date(current_year,current_month,current_date) + relativedelta(months = -1)
                
                DATETIME_FORMAT = "%Y-%m-%d"
                dt_before_1month = str(date_before_1month)
                
                date_before_1month_year=int(dt_before_1month[:4])
                
                date_before_1month_month=int(dt_before_1month[5:7])
                
                date_before_1month_date=int(dt_before_1month[8:10])
                
           #-----------------End of Date before 1 month-------------------------------------     
           
           #-----------------Start Date and End Date of previous Month-------------------------
                start_date = date(date_before_1month_year,date_before_1month_month,1)
                
                last_date = self.last_day_of_month(cr,uid,ids,date_before_1month_year,date_before_1month_month)
                
                
                
           #-----------------End of Start Date and End Date of previous Month-------------------------
                
           
           
           #-----------------Date of Joining-------------------------------------
                
                date_of_joining = c.joining_date
                dt_of_joining = datetime.datetime.strptime(date_of_joining, DATETIME_FORMAT).date()
                
                emp_joining_year=int(c.joining_date[:4])
                emp_joining_month=int(c.joining_date[5:7])
                emp_joining_date=int(c.joining_date[8:10])
                from dateutil.relativedelta import relativedelta
                doj_format = date(emp_joining_year,emp_joining_month,emp_joining_date)
                
                
            #-----------------End of Date of Joining-------------------------------------  
                
                if doj_format not in (start_date,last_date):
                    
                    search_allocated_records = self.pool.get('hr.holidays').search(cr, uid, [('type','=','add'),('holiday_type','=','employee'),('employee_id','=',c.id)])
                    
                    for u in self.pool.get('hr.holidays').browse(cr, uid, search_allocated_records):
                        
                        
                        cr.execute("update hr_holidays set number_of_days_temp = number_of_days_temp+2 where employee_id = %(val1)s and type = 'add' and state='validate'",{'val1':c.id})
                        cr.execute("update hr_holidays set number_of_days = number_of_days_temp where employee_id = %(val1)s and type = 'add' and state='validate'",{'val1':c.id})
                        
    def allocate_leaves_to_mothers(self,cr,uid,ids,context=None):    #### Scheduler for Allocation of 1 extra leave to mothers based on the number of children
        
        
        search_new_emp_record = self.pool.get('hr.employee').search(cr, uid, [('id','>',0)])
            
             
            
        for t in self.pool.get('hr.employee').browse(cr,uid,search_new_emp_record):
        
            employee_id=t.id
            
            emp_gender=t.gender
            if emp_gender == 'female':
                search_children = self.pool.get('children.details').search(cr, uid, [('child_id','=',employee_id),('age','<',14)])
                
                for y in self.pool.get('children.details').browse(cr, uid, search_children[0:4]):
                    
                    search_allocated_holidays = self.pool.get('hr.holidays').search(cr, uid, [('employee_id','=',employee_id),('type','=','add'),('state','=','validate')])
                    
                    for z in self.pool.get('hr.holidays').browse(cr, uid, search_allocated_holidays):
                        no_of_days = z.number_of_days_temp
                        no_of_days += 1
                        
                        cr.execute("update hr_holidays set number_of_days_temp = number_of_days_temp+1 where employee_id = %(val)s and type = 'add' and state='validate'",{'val':employee_id})
                        cr.execute("update hr_holidays set number_of_days = number_of_days_temp where employee_id = %(val)s and type = 'add' and state='validate'",{'val':employee_id})
                        
                    
        
        return True
    
    def onchange_date(self,cr,uid,ids,date_from):
        if date_from:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            a=from_dt.weekday()
            return {'value' : {'day':str(a)}}
        return {'value' : {'day':False}}
    
    
leaves_calendar()

class holidays_calendar(osv.osv):
    _name = "holidays.calendar"
    _description = "Holidays Calendar"
    _columns = {
        
        'name': fields.char('Holidays Calendar Name', size=124, required=True),
        'location':fields.selection([('Mumbai', 'Mumbai'),('Goa','Goa')],'Location'),
        'holidays_line':fields.one2many('leaves.calendar','holiday_id'," ", size=124),
         
        }
 
holidays_calendar()


class hr_holidays_payroll_code(osv.osv):
	_name = 'hr.holidays.payroll.code'
	_columns = {
		'name' : fields.char('Code'),
		'description' : fields.char('Description'),
}

class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"
    _columns = {
		'payroll_code' : fields.many2one('hr.holidays.payroll.code','Payroll Code'), 
        'leave_code' : fields.char('Leave Code', size=4),
}
    
class hr_contract(osv.osv):
    _inherit = "hr.contract"
    _description = 'Employee Contract'
    _columns = {
		'holidays_id' : fields.many2one('holidays.calendar','Holidays Calendar', size=124),
        'nutritional_allowance' : fields.integer('Nutritional Allowance', size=124),
        'attendance_incentive' : fields.integer('A.I. All', size=124),
        'da_lta_fa' : fields.integer('DA/LTA/FA', size=124),
        'special_allowance' : fields.integer('Special Allowance', size=124),
        'hra' : fields.integer('House Rent Allowance', size=124),
        'emi_amount': fields.integer('Loan EMI', size=124),
        'bonus_amount': fields.float('Bonus Amount', size=124),
        'telephone_allowance_line' : fields.one2many('telephone.allowance', 'contract_id', 'Telephone Allowance', size=64), 
        'result_telephone_allowance': fields.integer('Resultant Telephone Allowance', size=64),
        'irt' : fields.float('IRT', size=64),  
        'advance': fields.float('Salary Advance', size=64),
        'leave_allowance_applicable':fields.boolean('Leave Allowance Applicable', size=64),
        'performance_bonus_applicable':fields.boolean('Performance Bonus Applicable', size=64),
}
hr_contract()

class telephone_allowance(osv.osv):
    
    _name= "telephone.allowance"
    _description = "Telephone Allowance"
    _order = "updation_date"
    from datetime import datetime
    _columns = {
        'contract_id' : fields.many2one('hr.contract','Contracts', size=124),
        'amount' : fields.integer('Amount', size=124),
        
        'updation_date' : fields.date('Updation Date'),
        'month' : fields.selection([('1', 'January'),('2', 'February'),('3', 'March'),('4', 'April'),('5', 'May'),('6', 'June'),('7', 'July'),('8', 'August'),('9', 'September'),('10', 'October'),('11', 'November'),('12', 'December')], "Month", readonly="True"),
        'year': fields.selection([(num, str(num)) for num in range(1900, (datetime.now().year)+100 )], 'Year', readonly="True"), 
}
    _defaults = {
                 'updation_date' : fields.date.context_today,
                 }
    
    def onchange_updation_date(self,cr,uid,ids,updation_date):
        if updation_date:
            
            month = int(updation_date[5:7])
            year = int(updation_date[:4])
            
            return {'value' : {'month':str(month),'year':year}}
        return {'value' : {'month':False, 'year':False}}
telephone_allowance()

class hr_attendance_table(osv.osv):
    _name='hr.attendance.table'
    _description = 'Attendance Table'
    _columns = {
        'batch_attendance_id':fields.many2one('attendance.batch', size=64),
        'date_from':fields.date('Date From'),
        'date_to':fields.date('Date To'),
        'name':fields.char('Attendance Slip', size=124),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True), 
        'attendance_line':fields.one2many('hr.attendance.table.line','attendance_table','Attendance Lines', size=124),       
}
    _defaults={
         'name': lambda obj, cr, uid, context: '/',   
               }
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'hr.attendance.table') or '/'
        return super(hr_attendance_table, self).create(cr, uid, vals, context=context)
    
    def recompute_attendance(self, cr, uid, ids, context=None):
        for attendance in self.browse(cr, uid, ids,context=None):
            contract_ids = self.pool.get('hr.payslip').get_contract( cr, uid, attendance.employee_id, attendance.date_from, attendance.date_to, context=None)
            contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context) and self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context)[0] or False
            for line in attendance.attendance_line:
                        date = line.date
                        date1= datetime.strptime(date,'%Y-%m-%d')
                        j ='A'
                        if line.attendance:
                            j= 'P'
                        
                        absent_info = ''
                        final_result = ''
                        
                        if contract_obj:
                            search_for_weekly_off = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract_obj.working_hours, date1, context)
                            search_for_even_saturday = self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date1),('type','=','even_sat')])
                            search_for_holiday=self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date1),('type','<>','even_sat')])
                            search_for_leave=self.pool.get('hr.holidays').search(cr, uid, [('employee_id','=',attendance.employee_id.id),('state','=','validate'),('type','=','remove'),('date_from','<=',date),('date_to','>=',date)])
                            if search_for_even_saturday:
                                search_for_weekly_off = 0.0
                            if search_for_leave:  
                                      absent_info = self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.payroll_code.name or self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.name
                                      if  absent_info == "Unpaid":
                                          absent_info = 'UL'
                                      else:
                                          absent_info = 'PL'
                            elif search_for_holiday:
                                    absent_info = 'H'
                            elif not search_for_weekly_off:
                                absent_info = 'WO'
                        if absent_info:
                            if j== 'P' and absent_info=='H': 
                                final_result = 'HH'                
                            else:
                                 final_result = absent_info       
                        else:
                            if j== 'P':        
                                        final_result ='P'
                            else:
                                       final_result ='A'  
                        if j == 'P':
                           attendance_line_id = self.pool.get('hr.attendance.table.line').write(cr,uid,line.id,{
                                                                                                        
                                  
                                  'absent_info':absent_info,'final_result':final_result})
                        else:
                                 self.pool.get('hr.attendance.table.line').write(cr,uid,line.id,{
                                
                                
                                  'absent_info':absent_info,'final_result':final_result})   
                        
                        
        
        return True
    
    
    
    def generate_attendance(self, cr, uid, ids, context=None):
        for z in self.browse(cr, uid, ids, context=None):
            employee_id=z.employee_id.id
            date_from=z.date_from
            date_to=z.date_to
            from_date = int(date_from[8:10])
            month = int(date_from[5:7])
            year = int(date_from[:4])
            to_date = int(date_to[8:10])
            
            date_dict = {}
            d=1
            for i in range(1,to_date+1):
                    
                   date_dict[i] = datetime.date(year,month ,i)
                   
                   search_attendance_records = self.pool.get('hr.attendance.table').search(cr, uid, [('employee_id','=', employee_id),('date_from','=', date_from),('date_to','=',date_to)])
                   
                   
                   
                   attendance_line_id = self.pool.get('hr.attendance.table.line').create(cr,uid,{'employee_id': employee_id, 'attendance_table':z.id, 'date':date_dict[d], 'final_result':'A'})
                   
                   x=self.pool.get('hr.attendance.table.line').browse(cr, uid, attendance_line_id)
                   
                   
                   emp_sign_in=''
                   emp_sign_out=''
                   attendance_records=self.pool.get('hr.attendance').search(cr, uid, [('employee_id','=',employee_id)])
                   for h in self.pool.get('hr.attendance').browse(cr, uid, attendance_records):

                        emp_action=h.action
                        
                        emp_datetime=h.name
                        
                        date1=emp_datetime[:10]
                        
                        
                        
                        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                        from_dt = datetime.datetime.strptime(emp_datetime, DATETIME_FORMAT)
                        
                        if (date1==x.date and (emp_action=='sign_in' or emp_action=='sign_out')):
                            if emp_action=='sign_in':
                                
                                emp_sign_in=emp_datetime
                                
                            if emp_action=='sign_out':
                                
                                emp_sign_out=emp_datetime
                            if emp_sign_in and emp_sign_out:
                                
                                self.pool.get('hr.attendance.table.line').write(cr,uid,x.id, {'attendance':True, 'final_result':'P', 'sign_out_time': emp_sign_out, 'sign_in_time':emp_sign_in})
                    
                   for t in self.browse(cr, uid, ids[0]).attendance_line:
                            final_result=t.final_result
                            date=t.date
                          
                            if final_result== 'A':
                                
                               leave_search=self.pool.get('hr.holidays').search(cr,uid,[('employee_id','=',employee_id),('date_from','<=',date),('date_to','>=',date),('state','=','validate')])
                               
                               if leave_search:
                                   self.pool.get('hr.attendance.table.line').write(cr,uid,t.id, {'absent_info':'PL','final_result':'PL'}) 
                                    
                            emp_obj =   self.pool.get('hr.employee').browse(cr,uid,employee_id)
                            contract_ids = self.pool.get('hr.payslip').get_contract( cr, uid, emp_obj, date_from, date_to, context=None)
                            contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context) and self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context)[0] or False
                            
                            search_for_weekly_off = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract_obj.working_hours, date_dict[d], context)
                            search_for_holiday=self.pool.get('leaves.calendar').search(cr, uid, [('holiday_id','=',contract_obj.holidays_id.id),('date_from','=',date_dict[d])])        
                   
                   
                   if not search_for_weekly_off:
                                
                                self.pool.get('hr.attendance.table.line').write(cr,uid,t.id, {'absent_info':'WO','final_result':'WO'})
                   if search_for_holiday:
                                             
                                self.pool.get('hr.attendance.table.line').write(cr,uid,t.id, {'absent_info':'H','final_result':'H'})
                   d+=1
                        
                    
                        
            
hr_attendance_table()


class hr_attendance_table_line(osv.osv):
    _name = 'hr.attendance.table.line'
    _description = 'Attendance Table'
    _columns = {
    'attendance_table':fields.many2one('hr.attendance.table','Attendance'),
	'name' : fields.char('Name'),
    'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
    'date': fields.date('Day of the Month'),
	'attendance': fields.boolean('Absent/Present'),
	'absent_info': fields.char('Information', size=124),
	'final_result': fields.char('Result'),
    'sign_in_time':fields.datetime('Sign-In Time'),
    'sign_out_time':fields.datetime('Sign-Out Time'),
    }
       
    def fetch_attendance_info(self,cr,uid,ids,context=None):
	 	for p in self.browse(cr, uid, ids,context=None):
						 leave_id=p.id
						 employee_id=p.employee_id.id
						 specific_date=p.date
						 attendance_status=p.attendance
						 absent_info=p.absent_info
						 aa = datetime.strptime(specific_date,"%Y-%m-%d")
						 contract_ids = self.pool.get('hr.payslip').get_contract( cr, uid, p.employee_id, specific_date, specific_date, context=None)
						 contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context) and self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context)[0] or False
						 if contract_obj:
						 	search_for_weekly_off = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract_obj.working_hours, aa, context)
                        
						 search_for_holiday=self.pool.get('leaves.calendar').search(cr, uid, [('employee_id','=',employee_id),('date_from','=',specific_date)])
						
						 search_for_leave=self.pool.get('hr.holidays').search(cr, uid, [('employee_id','=',employee_id),('state','=','validate'),('type','=','remove'),('date_from','<=',specific_date),('date_to','>=',specific_date)])
									            
						 if search_for_leave:
						 	
						 	res = self.pool.get('hr.holidays').browse(cr, uid, search_for_leave, context=context)[0].holiday_status_id.payroll_code.name
						 	self.write(cr,uid,leave_id,{'absent_info':res}) 
									 			 						  
						 elif search_for_holiday:
							
							self.write(cr,uid,leave_id,{'absent_info':'H'})
							
						 elif not search_for_weekly_off:
						 	
						 	self.write(cr,uid,leave_id,{'absent_info':'WO'})
						 
						 
						 for q in self.browse(cr, uid, ids,context=None):
								absent_info_new=q.absent_info
							        	
						 if absent_info_new: 
						 	if attendance_status==True and absent_info_new=='H':
						 	
						 		self.write(cr,uid,leave_id,{'final_result':'P'})
					 		else:
					 			self.write(cr,uid,leave_id,{'final_result':absent_info_new})
					 	 else:
					 		if attendance_status:
					 			self.write(cr,uid,leave_id,{'final_result':'P'})
					 		else:
					 			self.write(cr,uid,leave_id,{'final_result':'A'})	 
						 		  
		return True				 
 
class absent_info(osv.osv):
    _name = "absent.info"
    _description = "Absent Information"
    _columns = {
        'name':fields.char('Absent Information', size=124),

        }

absent_info()

class hr_payslip(osv.osv):

    _inherit = 'hr.payslip'
    
    _columns = {
         'number_of_months_worked':fields.integer('Number of Months worked', size=64),
                }
    

    def diff_month(self,cr,uid,ids,d1,d2):
        return (d1.year - d2.year)*12 + d1.month - d2.month
    
    def compute_sheet(self, cr, uid, ids, context=None):
        slip_line_pool = self.pool.get('hr.payslip.line')
        sequence_obj = self.pool.get('ir.sequence')
        for payslip in self.browse(cr, uid, ids, context=context):
            form_id = payslip.id
            date_from = payslip.date_from
            date_to = payslip.date_to
            employee_id = payslip.employee_id.id
            
            search_employee = self.pool.get('hr.employee').search(cr, uid, [('id','=',employee_id)])
            
            
            for e in self.pool.get('hr.employee').browse(cr, uid, search_employee):
                date_of_joining = e.joining_date
                
                
            from datetime import datetime
            date_to_payslip = datetime.strptime(payslip.date_to,"%Y-%m-%d")
            emp_joining_date = datetime.strptime(e.joining_date,"%Y-%m-%d")
            
            months_difference = self.diff_month(cr,uid,ids,date_to_payslip,emp_joining_date)
            
            
            
            
            
            self.write(cr, uid, payslip.id, {'number_of_months_worked': months_difference})
            leave_search=self.pool.get('hr.holidays').search(cr,uid,[('employee_id','=',employee_id),('type','=','remove'),('state','=','validate')])
            
            for c in self.pool.get('hr.holidays').browse(cr,uid,leave_search):
                leave_from_date = c.date_from
                leave_to_date = c.date_to
                
            search_leaves_between_payroll_dates = self.pool.get('hr.holidays').search(cr,uid,[('employee_id','=',employee_id),('type','=','remove'),('state','=','validate'),(('date_from','>=',payslip.date_from) and ('date_from','<=',payslip.date_to)), (('date_to','>=',payslip.date_from) and ('date_to','<=',payslip.date_to)),('is_apply_leave_allowance','=',True)])
            
            search_contract_record = self.pool.get('hr.contract').search(cr,uid,[('employee_id','=',employee_id)])
            for r in self.pool.get('hr.contract').browse(cr,uid,search_contract_record):
                
                if search_leaves_between_payroll_dates:     
                    self.pool.get('hr.contract').write(cr,uid,r.id,{'leave_allowance_applicable':True})
                else:
                    self.pool.get('hr.contract').write(cr,uid,r.id,{'leave_allowance_applicable':False})
                    
            for u in self.pool.get('hr.employee').browse(cr, uid, search_employee):
                number_months_worked = u.no_of_months_worked
                
                date_joing=u.joining_date
                date_from_year = int(u.joining_date[:4])
                date_from_month = int(u.joining_date[5:7])
                date_from_date = int(u.joining_date[8:10])
                from datetime import date
                from dateutil.relativedelta import relativedelta
                date_after_6months = date(date_from_year,date_from_month,date_from_date) + relativedelta(months = +6)
                
                
            if number_months_worked >= 6:
                
                start_date_lst=[]
                end_date_lst=[]
                start_date_lst.append('2013-01-01')
                start_date_lst.append('2013-03-01')
                start_date_lst.append('2013-06-01')
                start_date_lst.append('2013-09-01')
                end_date_lst.append('2013-03-01')
                end_date_lst.append('2013-06-01')
                end_date_lst.append('2013-09-01')
                end_date_lst.append('2013-12-01')
                 
                i=0
                
                
                for i in range(0,len(start_date_lst)):
                    
                    
                    if start_date_lst[i] < str(date_after_6months) < end_date_lst[i]:
                        next_month_for_bonus_date=end_date_lst[i+1]
                        payslip_genration_month=next_month_for_bonus_date[5:7]
                        
                        if payslip.date_from[5:7] == payslip_genration_month:
                           self.pool.get('hr.contract').write(cr,uid,r.id,{'performance_bonus_applicable':True})
                        else:
                           self.pool.get('hr.contract').write(cr,uid,r.id,{'performance_bonus_applicable':False}) 
                
            
            contract_id = payslip.contract_id.id
            contract_search = self.pool.get('hr.contract').search(cr, uid, [('employee_id','=',payslip.employee_id.id)])
            contract_end_dates = []
            for g in self.pool.get('hr.contract').browse(cr,uid,contract_search):
                contract_date_end = g.date_end
                contract_end_dates.append(contract_date_end)
                
            max_contract_end_date = max(contract_end_dates)
            
            
            if not contract_id:
                raise osv.except_osv(('Warning!'),("No valid contract exists for employee %s as his previous contract has expired on %s")%(payslip.employee_id.name, max_contract_end_date))
                
            
            date_month = date_from[5:7]
            
            
            search_sick_records = self.pool.get('hr.attendance.table.line').search(cr, uid, [('employee_id','=',payslip.employee_id.id),('date','<=',payslip.date_to)]) 
            
            sorted_sick_records = sorted(search_sick_records, key=int, reverse=True)
            
            date_list = []
            for y in self.pool.get('hr.attendance.table.line').browse(cr , uid, sorted_sick_records):
                final_result = y.final_result
                date_to_attendance = y.date
                
                if final_result == 'P':
                    desc_date = y.date
                    
                    date_list.append(y.date)
            
            last_date_present = date_list[0]
            DATETIME_FORMAT = "%Y-%m-%d"
            
            from datetime import datetime
            date11 = datetime.strptime(date_to,"%Y-%m-%d")
            date22 = datetime.strptime(last_date_present,"%Y-%m-%d")
            
            
            diff_months = self.diff_month(cr, uid, ids, date11, date22)
            
            
            
            
            
            payslip_month = int(date_from[5:7])
            
            
            search_contract = self.pool.get('hr.contract').search(cr, uid, [('id','=',payslip.contract_id.id)]) 
            
            for r in self.pool.get('hr.contract').browse(cr, uid, search_contract):
                resultant_ta = r.result_telephone_allowance
            telephone_allowance_search = self.pool.get('telephone.allowance').search(cr, uid, [('contract_id','=',payslip.contract_id.id)])
            if telephone_allowance_search:
                optimal_telephone_allowance_search = self.pool.get('telephone.allowance').search(cr, uid, [('contract_id','=',payslip.contract_id.id),('updation_date','<=',payslip.date_from)])
                
                month=[]
                i=0
                for s in self.pool.get('telephone.allowance').browse(cr, uid, optimal_telephone_allowance_search):
                    amount = s.amount
                    effective_date = s.updation_date
                    effective_month = int(effective_date[5:7])
                    month.append(effective_date)
                    
                    
                    i+=1 
                    
                    
                    
                
                max_value = max(month)
                
                tele_allow_search = self.pool.get('telephone.allowance').search(cr, uid, [('updation_date','=', max_value)])
                
                for n in self.pool.get('telephone.allowance').browse(cr, uid, tele_allow_search):
                    final_amount = n.amount
                self.pool.get('hr.contract').write(cr, uid,payslip.contract_id.id,{'result_telephone_allowance' :final_amount })
            
            loan_id = self.pool.get('hr.employee.loan').search(cr, uid,[('employee_id','=',payslip.employee_id.id),('state','=','progress')])
            if loan_id:
               line_id = self.pool.get('hr.employee.loan.line').search(cr, uid,[('emi_date','>=',payslip.date_from),('emi_date','<=',payslip.date_to),('loan_id','=',loan_id[0])])
               
               if line_id :
                   self.pool.get('hr.employee.loan.line').write(cr, uid,line_id[0],{'payslip_id' :payslip.id }) 
                   
                      
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)

            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            if payslip.contract_id:
                
                contract_ids = [payslip.contract_id.id]
            else:
                
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
            
            self.write(cr, uid, [payslip.id], {'line_ids': lines, 'number': number,}, context=context)
            search_payslip_line = self.pool.get('hr.payslip.line').search(cr, uid, [('slip_id','=',payslip.id),('code','=','NET')])
            
            for k in self.pool.get('hr.payslip.line').browse(cr, uid, search_payslip_line):
                slip_line_id = k.id
                
                net_amount = k.amount
                
                if diff_months > 3:
                    final_net_amount = ((net_amount * 60)/100)
                    
                    self.pool.get('hr.payslip.line').write(cr, uid, slip_line_id, {'amount':final_net_amount})
                    
        return True
    
    
    

    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
       """
       @param contract_ids: list of contract id
       @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
       """
       print "testing"
       def was_on_leave(employee_id, datetime_day, context=None):
           res = False
           day = datetime_day.strftime("%Y-%m-%d")
           holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
           
           if holiday_ids:
               res = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
           return res
       res = []
       
       for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
           loan_id = self.pool.get('hr.employee.loan').search(cr, uid,[('employee_id','=',contract.employee_id.id),('loan_type','=','loan')])
           advance_id = self.pool.get('hr.employee.loan').search(cr, uid,[('employee_id','=',contract.employee_id.id),('loan_type','=','advance')])
           if loan_id:
             loan_line_id = self.pool.get('hr.employee.loan.line').search(cr, uid,[('emi_date','>=',date_from),('emi_date','<=',date_to),('loan_id','=',loan_id[0])])
             if loan_line_id :
                 loan_line_obj = self.pool.get('hr.employee.loan.line').browse(cr, uid,loan_line_id[0])
                 self.pool.get('hr.contract').write(cr,uid,contract.id,{'emi_amount':loan_line_obj.emi_amount})
                 
                 self.pool.get('hr.contract').write(cr,uid,contract.id,{'advance':0.00})
                 print "loan_line_obj.emi_amount",loan_line_obj.emi_amount
           elif advance_id:
             advance_line_id = self.pool.get('hr.employee.loan.line').search(cr, uid,[('emi_date','>=',date_from),('emi_date','<=',date_to),('loan_id','=',advance_id[0])])
             if advance_line_id :
                 advance_line_obj = self.pool.get('hr.employee.loan.line').browse(cr, uid,advance_line_id[0])
                 self.pool.get('hr.contract').write(cr,uid,contract.id,{'advance':advance_line_obj.emi_amount})
                 
                 self.pool.get('hr.contract').write(cr,uid,contract.id,{'emi_amount':0.00})
                   
           elif loan_id and advance_id:
                self.pool.get('hr.contract').write(cr,uid,contract.id,{'advance':advance_line_obj.emi_amount})
                self.pool.get('hr.contract').write(cr,uid,contract.id,{'emi_amount':loan_line_obj.emi_amount})
            
           else:
                 self.pool.get('hr.contract').write(cr,uid,contract.id,{'emi_amount': 0.0})
                 self.pool.get('hr.contract').write(cr,uid,contract.id,{'advance':0.0})
                   
           if not contract.working_hours:
               continue
           P = {
                    'name': _("Normal Working Days paid at 100%"),
                         'sequence': 1,
                         'code': 'WORK100',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
               }
           WO = {
                         'name': _("Weekly Offs"),
                         'sequence': 3,
                         'code': 'weekly',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                     
                     }
           A = {
                      'name': _("Days Marked as Absent"),
                         'sequence': 4,
                         'code': 'absent',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                    
                    }
           worked = {
                         'name': _("Goa-Days on the Ground"),
                         'sequence': 2,
                         'code': 'WORK200',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                         }
               
               
           PL = {
                         'name': _("Paid Leaves taken"),
                         'sequence': 5,
                         'code': 'pl',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                     
                     }
           UL = {
                        'name': _("Unpaid Leaves taken"),
                         'sequence': 6,
                         'code': 'Unpaid',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                     }
           H = {
                    'name': _("Paid Holidays"),
                         'sequence': 7,
                         'code': 'paid_holiday',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                    }
           HH = {
                      'name': _("Worked on a Paid Holiday"),
                         'sequence': 8,
                         'code': 'worked_paid_holiday',
                         'number_of_days': 0.0,
                         'number_of_hours': 0.0,
                         'contract_id': contract.id,
                     }
           att_records = {
                            'P' :P,
                            'A' :A,
                            'worked':worked,
                            'WO':WO,
                            'PL':PL,
                            'UL':UL,
                            'H':H,
                            'HH':HH
                              }
           from datetime import datetime
           day_from = datetime.strptime(date_from,"%Y-%m-%d")
           day_to = datetime.strptime(date_to,"%Y-%m-%d")
           nb_of_days = (day_to - day_from).days + 1
           attendance_line = self.pool.get('hr.attendance.table.line').search(cr, uid, [('employee_id','=',contract.employee_id.id),('date','>=',date_from),('date','<=',date_to)])
           
           leaves = {}
           
           for day in range(0, nb_of_days):
             if  not contract.employee_id.attendance: 
               att_id = self.pool.get('hr.attendance.table.line').search(cr, uid, [('employee_id','=',contract.employee_id.id),('date','=',day_from +timedelta(days=day))])
               for att_obj in self.pool.get('hr.attendance.table.line').browse(cr,uid, att_id):
                   if att_obj.attendance == True:
                       worked['number_of_days'] += 1.0
                       worked['number_of_hours'] += 8.0
                   if att_obj.attendance == True and att_obj.final_result == 'HH':
                       
                       P['number_of_days'] += 1.0
                       P['number_of_hours'] += 8.0
                   if att_obj.attendance == False and att_obj.absent_info == 'WO' and att_obj.final_result == 'HH':
                       
                       WO['number_of_days'] += 1.0
                       WO['number_of_hours'] += 8.0
                   if att_obj.attendance == False and att_obj.absent_info == 'Manual Attendance' and att_obj.final_result == 'HH':
                       
                       P['number_of_days'] += 1.0
                       P['number_of_hours'] += 8.0            
                   if att_obj.final_result in att_records:
                       att_records[att_obj.final_result]['number_of_days'] += 1.0
                       att_records[att_obj.final_result]['number_of_hours'] += 8.0
                   else:
                       att_records[att_obj.final_result] = {
                                                               'name': att_obj.final_result,
                                                               'sequence': 10,
                                                               'code': att_obj.final_result,
                                                               'number_of_days': 1.0,
                                                               'number_of_hours': 8.0,
                                                               'contract_id': contract.id,
                                                            }  
             else:
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                if working_hours_on_day:
                    
                    leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day), context=context)
                    if leave_type:
                        
                        if leave_type in leaves:
                            leaves[leave_type]['number_of_days'] += 1.0
                            leaves[leave_type]['number_of_hours'] += working_hours_on_day
                        else:
                            leaves[leave_type] = {
                                'name': leave_type,
                                'sequence': 5,
                                'code': leave_type,
                                'number_of_days': 1.0,
                                'number_of_hours': working_hours_on_day,
                                'contract_id': contract.id,
                            }
                    else:
                        
                        att_records['P']['number_of_days'] += 1.0
                        att_records['P']['number_of_hours'] += working_hours_on_day          
           leaves = [value for key,value in leaves.items()]            
           monthdays = {
                     'name': _("Days in the Month"),
                     'sequence': 100,
                     'code': 'MONTHDAYS',
                     'number_of_days': calendar.monthrange(day_from.year, day_from.month)[1],
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                        } 
           att_records['MONTHDAYS']=monthdays
           salarydays = {
                         'name': _("Salary Days in the Month"),
                                     'sequence': 100,
                                     'code': 'SALARYDAYS',
                                     'number_of_days': nb_of_days,
                                     'number_of_hours': 0.0,
                                     'contract_id': contract.id,
                         }
            
           
               
           l = [salarydays,att_records['MONTHDAYS'], att_records['P'], att_records['worked'], att_records['A'], att_records['PL'], att_records['WO'], att_records['UL'], att_records['H'], att_records['HH'],]            
       return l
   
    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                
                return res or 0.0
            
        class IrtLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0


        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                
                return res and res[0] or 0.0

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        inputs_obj = self.pool.get('hr.payslip.worked_days')
        obj_rule = self.pool.get('hr.salary.rule')
        irt_obj = self.pool.get('irt.table.line')
        irt_dict = {}
        #irt = irt_obj.browse(cr, uid, )
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        irt_obj = IrtLine(self.pool, cr, uid, payslip.employee_id.id, irt_dict)
        
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

        localdict = {'categories': categories_obj, 'rules': rules_obj, 'payslip': payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj, 'irt': irt_obj}
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        
        taxable_income_categ = self.pool.get('hr.salary.rule.category').search(cr, uid, [('name','=','Taxable Income')])
        for c in self.pool.get('hr.salary.rule.category').browse(cr, uid, taxable_income_categ):
            tax_categ_id = c.id
            
        
        taxable_income = self.pool.get('hr.salary.rule').search(cr, uid, [('category_id', '=', tax_categ_id)])
        
        
        
        
        
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict.update({'employee': employee, 'contract': contract})
            
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                
                    
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]
            for rule1 in obj_rule.browse(cr, uid, taxable_income, context=context):
                  
                 key = rule1.code + '-' + str(contract.id)
                 if obj_rule.satisfy_condition(cr, uid, rule1.id, localdict, context=context) and rule1.id not in blacklist:
                     #compute the amount of the rule
                     amount, qty, rate = obj_rule.compute_rule(cr, uid, rule1.id, localdict, context=context)
                     #check if there is already a rule computed with that code
                     previous_amount = rule1.code in localdict and localdict[rule1.code] or 0.0
                     #set/overwrite the amount computed for this rule in the localdict
                     tot_rule = amount * qty * rate / 100.0
                     localdict = _sum_salary_rule_category(localdict, rule1.category_id, tot_rule - previous_amount)
                     #create/overwrite the rule in the temporary results
                     
                     ti_amount = amount
                         
        
                      
        
        irt_search = self.pool.get('irt.table.line').search(cr, uid, [('a_from_value','<=',ti_amount) or (('a_from_value','<=',ti_amount),('a_to_value','>=',ti_amount))])
        
        for irt in self.pool.get('irt.table.line').browse(cr, uid, irt_search, context=context):
            localdict.update({'irt': irt})
            
            
        
        if irt_search :
            for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
                employee = contract.employee_id
                localdict.update({'employee': employee, 'contract': contract})
                
                
                
                
                for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                    key = rule.code + '-' + str(contract.id)
                    localdict['result'] = None
                    localdict['result_qty'] = 1.0
                    #check if the rule can be applied
                    if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                        #compute the amount of the rule
                        amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                        #check if there is already a rule computed with that code
                        previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                        #set/overwrite the amount computed for this rule in the localdict
                        tot_rule = amount * qty * rate / 100.0
                        
                        localdict[rule.code] = tot_rule
                        rules[rule.code] = rule
                        #sum the amount for its salary category
                        localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                        #create/overwrite the rule in the temporary results
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': rule.name,
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                        }
                    
                        
                    else:
                        #blacklist this rule and its children
                        blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]
                    
        result = [value for code, value in result_dict.items()]
        
        return result        
    
