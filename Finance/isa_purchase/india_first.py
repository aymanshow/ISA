from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from email.message import Message


from osv import fields, osv
from tools.translate import _
import StringIO
import cStringIO
import base64
import xlrd
import string
import calendar
from calendar import monthrange
import datetime


import base64
import datetime
import dateutil
import email
import logging
import pytz
import re
import time
import xmlrpclib
from email.message import Message

from openerp import tools
from openerp import SUPERUSER_ID
from openerp.addons.mail.mail_message import decode
from openerp.osv import fields, osv, orm
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _


class res_partner(osv.osv):
	_name = "res.partner"
	_description = "Contacts"
	_inherit = "res.partner"
	
	_columns = {
		'age':fields.integer('Age', size=64),	
		'volunteer': fields.boolean('Volunteer', help="Check this box if this contact is a Volunteer."),
		'list_submitted': fields.boolean('Contacts List Submitted', help="Check this box if this manager has submitted his contacts list."),
		'voter' : fields.boolean('Registered to vote'),
		'voting_history' : fields.selection([('Always','Always'),('Sometimes','Sometimes'),('Never','Never')],'Voting History'),
		'modi_selection' : fields.selection([('Yes','Yes'),('No','No'),('Neutral','Neutral')],'Modi for PM'), 
		'monetary' : fields.boolean('Willing to contribute money'),
		'volunteer_manager' : fields.many2one('res.partner','Managing Volunteer'),
		'child_ids': fields.one2many('res.partner', 'volunteer_manager', 'Children Candidates'),
		'list_not_submitted': fields.one2many('candidates.not.submitted', 'candidate_id', 'Children Candidates who have not submitted their list'),
		
		}
	
# 	def send_email(self,cr,uid,ids,context=None):
# 		for x in self.browse(cr,uid,ids,context=context):
# 			volunteer=x.volunteer
# 			list_submitted=x.list_submitted
# 			email=x.email
# 			name=x.name
# 			volunteer_manager=x.volunteer_manager.id
# 			children=x.volunteer_manager.child_ids[0].name
# 			
# 			candidates_no_list=self.pool.get('res.partner').search(cr,uid,[('volunteer_manager','=',volunteer_manager),('list_submitted','=',False)])
# 			for wt in self.pool.get('res.partner').browse(cr,uid,candidates_no_list):
# 				candidate_name=wt.id
# 				name=wt.name
# 				candidate_volunteer=wt.volunteer_manager.id
# 				candidate_phone=wt.phone
# 				candidate_email=wt.email
# 				
# 				sheet_id=self.pool.get('candidates.not.submitted').create(cr, uid, {'name':candidate_name, 'phone':candidate_phone, 'email':candidate_email, 'volunteer_manager':candidate_volunteer, 'candidate_id':candidate_volunteer})
# 			
# 			current_user=self.pool.get('res.users').search(cr,uid,[('id','=',uid)])
# 			for h in self.pool.get('res.users').browse(cr,uid,current_user):
# 				email_current_user=h.email
# 			if volunteer==True and list_submitted==False:
#  				email_template_obj = self.pool.get('email.template')
#      			template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','res.partner')], context=context)
#      			
#      			 
#      			if template_ids:
#      				mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], ids[0], force_send=True, context=context)
#      				mail_id = email_template_obj.send_mail(cr, uid, template_ids[1], ids[0], force_send=True, context=context)
     			
		#return True
res_partner()	

class mail_thread(osv.osv):
	_name = "mail.thread"
	_description = "Mails"
	_inherit = "mail.thread"
	
	_columns={
			
			}
	
	def _get_user(self, cr, uid, context=None):
   		res={}
   		return self.pool.get('res.users').browse(cr,uid,uid).id
      	
	
	_defaults = {
			
			}
	
	def import_attendance(self,cr,uid,file_data,context=None):
		
		val=base64.decodestring(file_data)
		
		fp=StringIO.StringIO()
		
		fp.write(val)
		wb=xlrd.open_workbook(file_contents=fp.getvalue())
		sheet=wb.sheet_by_index(0)
		
 		
		for i in range(2,3):
			version=sheet.row_values(i,0,sheet.ncols)[13]
        	
        	if version=='':
        		sheet_id=self.pool.get('v1.excel').create(cr, uid, {'file':file_data,'comment':'V1: Regular import'})
        	elif version=='v2.0':
        		manager_name =sheet.row_values(3,0,sheet.ncols)[2]
          		manager_mob =sheet.row_values(4,0,sheet.ncols)[2]
            	manager_email =sheet.row_values(5,0,sheet.ncols)[2]
            	manager= False   
             	if manager_email:
                        manager = self.pool.get('res.partner').search(cr,uid,[('email','=',manager_email)])
                elif manager_mob:
						manager = self.pool.get('res.partner').search(cr,uid,[('mobile','=',manager_mob)])
		else:
					manager = self.pool.get('res.partner').search(cr,uid,[('name','=',manager_name)]) 

             	manager_id=False
             	for ml in self.pool.get('res.partner').browse(cr,uid,manager):
			 		manager_id=ml.id
			 		
		
			 			
                 
            	if manager_name=='PLEASE FILL THIS':
                		if manager_mob=='PLEASE FILL THIS':
                    			if manager_email=='PLEASE FILL THIS':
                        			sheet_id=self.pool.get('v1.excel').create(cr, uid, {'file':file_data,'comment':'V2: Error in Manager details'})
                        		
                        			
             
            	else:
                 		if not manager_id:
			 					  manager_id = self.pool.get('res.partner').create(cr,uid,{'name': manager_name, 'mobile': manager_mob, 'email': manager_email})
			 		
                		for i in range(7,sheet.nrows):
                    			contact_name =sheet.row_values(i,0,sheet.ncols)[1]
                    			contact_age =sheet.row_values(i,0,sheet.ncols)[2]
                    			address =sheet.row_values(i,0,sheet.ncols)[3]
                    			city =sheet.row_values(i,0,sheet.ncols)[4]
                    			state =sheet.row_values(i,0,sheet.ncols)[5]
                    			pincode =sheet.row_values(i,0,sheet.ncols)[6]
                    			mobile =sheet.row_values(i,0,sheet.ncols)[7]
                    			email =sheet.row_values(i,0,sheet.ncols)[8]
                    			modi_selection =sheet.row_values(i,0,sheet.ncols)[9]
                     
                    			voter =sheet.row_values(i,0,sheet.ncols)[10]
                    			voting_history =sheet.row_values(i,0,sheet.ncols)[11]
                    
                    			volunteer_manager =sheet.row_values(i,0,sheet.ncols)[12]
                    
                    			
                      
                     
                    			contact_id = False
                    			if email:
                        			contact_id = self.pool.get('res.partner').search(cr,uid,[('email','=',email)])   
                    			if not contact_id and mobile:
                            			contact_id = self.pool.get('res.partner').search(cr,uid,[('mobile','=',mobile)])
                    			if not contact_id:
                         			contact_id = self.pool.get('res.partner').search(cr,uid,[('name','=',contact_name)]) 
                         			
                       
                                 
                          
                    
                    			
                      
                      
                    			state_name = self.pool.get('res.country.state').search(cr,uid,[('name','=',state)])
                    			
                    			for tl in self.pool.get('res.country.state').browse(cr,uid,state_name):
                        			state_id=tl.id
                        			
                          
                    			country_name = self.pool.get('res.country').search(cr,uid,[('name','=','India')])
                    			
                    			for cl in self.pool.get('res.country').browse(cr,uid,country_name):
                        			country_id=cl.id
                        			    
                    			if not state_name:
                        			state_id= self.pool.get('res.country.state').create(cr,uid,{'name': state, 'code': 1, 'country_id':country_id})
                        			
                      
                    			if not contact_id: 
                        			contact_id = self.pool.get('res.partner').create(cr,uid,{'name': contact_name, 'age': contact_age, 'city': city, 'zip': pincode, 'mobile': mobile, 'email': email, 'voting_history': str(voting_history), 'state_id': state_id, 'country_id': country_id, 'street2': address, 'volunteer_manager': manager_id, 'modi_selection': str(modi_selection)})
                        			contact_search = self.pool.get('res.partner').search(cr,uid,[('name','=',contact_name)])
                        			for pl_browse in self.pool.get('res.partner').browse(cr,uid,contact_search):
                               
                                 
                            				if voter=='Yes':
                               					self.pool.get('res.partner').write(cr,uid,pl_browse.id,{'voter': True})
                            				else:
                               					self.pool.get('res.partner').write(cr,uid,pl_browse.id,{'voter': False})
                                 
                             
                                 
                            				if volunteer_manager=='Yes':
                               					self.pool.get('res.partner').write(cr,uid,pl_browse.id,{'volunteer': True})
                            				else:
                               					self.pool.get('res.partner').write(cr,uid,pl_browse.id,{'volunteer': False})
                                 
                             
                            
                             
                            				volunteer=pl_browse.volunteer
                            				partner_id=pl_browse.id
                            				
                 
#                             				if volunteer==True:
#                                 
#                                 				email_template_obj = self.pool.get('email.template')
#                                 
#                                 				template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','res.partner'),('model_object_field.name', '=','volunteer')], context=context)
#                                 
#                                 
#                                 				for sl in self.pool.get('email.template').browse(cr,uid,template_ids):
#                                     					extra_field=sl.model_object_field.name
#                                     					   
#                                 				if template_ids:
#                                     					
#                                     					mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], partner_id, force_send=True, context=context)                
                                            
# 									 		email_template_obj=self.pool.get('email.template')
# 									 		template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','res.partner'),('model_object_field.name', '=','volunteer_manager')], context=context)
#                      				     	print template_ids, "TEMPLATE IDS"
#                              
#                                                                 
#                     		      			if template_ids:
#                                  
#                                 					mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], partner_id, force_send=True, context=context)       
                    			else:
                        							contact_id = contact_id[0]
                        
            
                email_template_obj = self.pool.get('email.template')
                template_ids = email_template_obj.search(cr, uid, [('model_id.model', '=','res.partner'),('model_object_field.name', '=','volunteer_manager')], context=context)
                print template_ids, "++++++++++TEMPLATE IDS+++++++++++++++++++++"
                if template_ids:
					mail_id = email_template_obj.send_mail(cr, uid, template_ids[0], manager_id, force_send=True, context=context)                  
        

    	
    

     
	def message_parse(self, cr, uid, message, save_original=False, context=None):
		msg_dict = {
		            'type': 'email',
		            'author_id': False,
		        }
		if not isinstance(message, Message):
		   if isinstance(message, unicode):
		                
		      message = message.encode('utf-8')
		   message = email.message_from_string(message)
		
		message_id = message['message-id']
		if not message_id:
		            
		   message_id = "<%s@localhost>" % time.time()
		   _logger.debug('Parsing Message without message-id, generating a random one: %s', message_id)
		msg_dict['message_id'] = message_id
		
		if message.get('Subject'):
		   msg_dict['subject'] = decode(message.get('Subject'))
		
		        
		msg_dict['from'] = decode(message.get('from'))
		msg_dict['to'] = decode(message.get('to'))
		msg_dict['cc'] = decode(message.get('cc'))
		
		if message.get('From'):
		   author_ids = self._message_find_partners(cr, uid, message, ['From'], context=context)
		   if author_ids:
		      msg_dict['author_id'] = author_ids[0]
		   msg_dict['email_from'] = decode(message.get('from'))
		partner_ids = self._message_find_partners(cr, uid, message, ['To', 'Cc'], context=context)
		msg_dict['partner_ids'] = [(4, partner_id) for partner_id in partner_ids]
		
		if message.get('Date'):
		   try:
		      date_hdr = decode(message.get('Date'))
		      parsed_date = dateutil.parser.parse(date_hdr, fuzzy=True)
		      if parsed_date.utcoffset() is None:
		                    
		         stored_date = parsed_date.replace(tzinfo=pytz.utc)
		      else:
		         stored_date = parsed_date.astimezone(tz=pytz.utc)
		   except Exception:
		         _logger.warning('Failed to parse Date header %r in incoming mail '
		                                'with message-id %r, assuming current date/time.',
		                                message.get('Date'), message_id)
		         stored_date = datetime.datetime.now()
		   msg_dict['date'] = stored_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
		
		if message.get('In-Reply-To'):
		   parent_ids = self.pool.get('mail.message').search(cr, uid, [('message_id', '=', decode(message['In-Reply-To']))])
		   if parent_ids:
		      msg_dict['parent_id'] = parent_ids[0]
		
		if message.get('References') and 'parent_id' not in msg_dict:
		   parent_ids = self.pool.get('mail.message').search(cr, uid, [('message_id', 'in',
		                                                                         [x.strip() for x in decode(message['References']).split()])])
		   if parent_ids:
		      msg_dict['parent_id'] = parent_ids[0]
		
		msg_dict['body'], msg_dict['attachments'] = self._message_extract_payload(cr, uid, message, save_original=save_original)
		return msg_dict
 
     
	def _message_extract_payload(self, cr, uid, message, save_original=False):
		"""Extract body as HTML and attachments from the mail message"""
		
		attachments = []
		body = u''
		
		if save_original:
			
			attachments.append(('original_email.eml', message.as_string()))
		if not message.is_multipart() or 'text/' in message.get('content-type', ''):
			encoding = message.get_content_charset()
			body = message.get_payload(decode=True)
			body = tools.ustr(body, encoding, errors='replace')
			if message.get_content_type() == 'text/plain':
				
				body = tools.append_content_to_html(u'', body, preserve=True)
		else:
			
			
			alternative = (message.get_content_type() == 'multipart/alternative')
			for part in message.walk():
				
				if part.get_content_maintype() == 'multipart':
					continue  
				filename = part.get_filename()  
				
				encoding = part.get_content_charset()  
				
				if filename or part.get('content-disposition', '').strip().startswith('attachment'):
					
					attachments.append((filename or 'attachment', part.get_payload(decode=True)))
					
					self.import_attendance(cr,uid,part.get_payload())
					
					continue
				
				if part.get_content_type() == 'text/plain' and (not alternative or not body):
					body = tools.append_content_to_html(body, tools.ustr(part.get_payload(decode=True),
																		 encoding, errors='replace'), preserve=True)
				
				elif part.get_content_type() == 'text/html':
					html = tools.ustr(part.get_payload(decode=True), encoding, errors='replace')
					if alternative:
						body = html
					else:
						body = tools.append_content_to_html(body, html, plaintext=False)
				
				else:
					
					
					attachments.append((filename or 'attachment', part.get_payload(decode=True)))
		return body, attachments




mail_thread()

class candidates_not_submitted(osv.osv):
	_name = "candidates.not.submitted"
	_description = "List of Candidates not submitted"
	
	
	_columns = {
		'candidate_id':fields.integer('Candidate ID', size=64),
		'name':fields.many2one('res.partner','Candidate Name', size=64),
		'phone':fields.char('Phone', size=64),
		'email':fields.char('Email', size=64),
		'volunteer_manager' : fields.many2one('res.partner','Managing Volunteer'),
		
		
		}
	
candidates_not_submitted()
class v1_excel(osv.osv):
    _name='v1.excel'
    _columns={
              'file':fields.binary("File Path:"),
              'file_name':fields.char('File Name:'),
              'welcome_email':fields.boolean('Send Welcome Email'),
              'state': fields.selection([('new', 'New'), ('in_progress', 'In Progress'), ('imported', 'Imported')], 'Status', track_visibility='onchange'),
              'comment':fields.char('Error'),
              }
    
    _defaults={
               'state':'new',
               }
    
    def import_excel(self,cr,uid,ids,context=None):
    	
		self.pool.get('contacts.import').import_excel(cr,uid,ids,context=context)
                                
        

        
v1_excel()
