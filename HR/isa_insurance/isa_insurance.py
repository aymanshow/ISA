from osv import osv
from osv import fields
import datetime
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import html2plaintext
class insurance_policy(osv.osv):
    _name='insurance.policy'
    def create(self, cr, uid, vals, context=None):
        res = super(insurance_policy, self).create(cr, uid, vals, context=context)
        hr_employee_obj = self.pool.get('hr.employee')
        hr_employee_obj.write(cr, uid, vals['emp_id'], {'renewal_date':vals['valid_to']}, context=context)
        return res   
    _columns={
              'policy_no':fields.char('Policy Number',required=True),
              'valid_from':fields.date('Valid From',readonly=True),
              'valid_to':fields.date('Valid To',required=True),
              'policy_attach':fields.binary('Policy Document Attachment'),
              'policy_value':fields.char('Policy Value'),
              'policy_provider_id':fields.many2one('res.partner','Policy Provider Name'),
              'premium_paid_line':fields.one2many('premium.inform','insurance_policy_ids','Premium Paid'),
              'emp_id':fields.many2one('hr.employee','Employee Name'),
              'gender':fields.selection([('male','Male'),('female','Female')],'Gender'),
              'age':fields.char('Age'),
              'dob':fields.date('Dob'),
              'position':fields.char('Position'),
              'department_id':fields.many2one('hr.department','Department'),
              'nominee_id':fields.char('Nominee'),
              'state':fields.selection([('draft','Draft'),('done','Confirmed')],'State'),
              }
    _defaults={
               'state':'draft',
               }
    def action_confirm(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state':'done'})
        return True
    def onchange_employee_id(self,cr,uid,ids,emp_id,context=None):
             res={}
             info=''
             drishtihr_obj=self.pool.get('hr.employee')
             line= drishtihr_obj.browse(cr,uid,emp_id)
             d1 = (datetime.utcnow()).date()
             if not line.birthday:
                 raise osv.except_osv(('Warning !'),('Please configure the employee birthday.'))
             else:
                 d2=line.birthday
                 d2 = datetime.strptime(d2,"%Y-%m-%d").date()
                 difference_in_days = abs((d1 - d2).days)
                 year=difference_in_days/365
                 month=(difference_in_days%365)/30
                 age=(str(year)+' year '+str(month)+' month')
             if not line.gender:
                raise osv.except_osv(('Warning !'),('Please configure the employee gender.'))
             else:
                pass
             if not line.birthday:
                raise osv.except_osv(('Warning !'),('Please configure the employee birthday.'))
             else:
                pass
             if not line.department_id:
                raise osv.except_osv(('Warning !'),('Please configure the employee department.'))
             else:
                pass
             if not line.job_id:
                raise osv.except_osv(('Warning !'),('Please configure the employee job.'))
             else:
                pass
             if not line.renewal_date:
                raise osv.except_osv(('Warning !'),('Please check the recruitment process in the stage of offer acceptance. or manually configure the insurance renewal date'))
             else:
                 date_joing=line.renewal_date
                 date_from_year = int(line.renewal_date[:4])
                 date_from_month = int(line.renewal_date[5:7])
                 date_from_date = int(line.renewal_date[8:10])
                 from datetime import date, timedelta
                 date_after_1day = date(date_from_year,date_from_month,date_from_date) + relativedelta(days = +1)
             if not line.nominee:
                raise osv.except_osv(('Warning !'),('Please configure the employee nominee in Employee form.'))
             else:
                pass
             res ={
                        'gender':line.gender,
                        'dob':line.birthday,
                        'position':line.job_id.name,
                        'department_id':line.department_id.id,
                        'age':age,
                        'nominee_id':line.nominee,
                        'valid_from':str(date_after_1day),
                      } 
             return {'value':res}
class premium_inform(osv.osv):
    _name='premium.inform'
    _columns={
              'date':fields.date('Date'),
              'installment_no':fields.char('Installment Number'),
              'amount':fields.float('Amount'),
              'state':fields.selection([('draft','Draft'),('done','Confirmed')],'State'),
              'insurance_policy_ids':fields.many2one('insurance.policy','Insurance Policy Ids'),
              }
class hr_employee(osv.osv):
    _name='hr.employee'
    _inherit='hr.employee'
    _columns={
              'nominee':fields.char('Nominee'),
              'policy_number':fields.char('Policy Number'),
              'renewal_date':fields.date('Renewal Date'),
              }
    def check_renewal_date(self, cr, uid, ids=False, context=None):
        lst=[]
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
#         emp_ids=self.search(cr,uid,('department_id','=','health and wealth'))
#         print'======emp_ids==',emp_ids
        cur_date = date.today() + relativedelta( days = +30 )
        cur_date=str(cur_date)
        cur_date1 = date.today() + relativedelta( days = +7 )
        before_7days=str(cur_date1)
        ids = self.search(cr,uid,['|',('renewal_date','=',cur_date),('renewal_date','=',before_7days)])
        certi_obj=self.browse(cr,uid,ids)
#         for val in certi_obj.browse(cr,uid,emp_ids):
#             lst.append(val.work_email)
        for rec in certi_obj:
            mail_mail = self.pool.get('mail.mail')
            if rec.renewal_date == before_7days:
                asunto ='The Insurance Policy is due for renewal on %s for employee %s %s' % (rec.renewal_date,rec.name,rec.work_email)
                body = '' 
                body += '<b>Dear User,'
                body += '<br/>'
                body += '<br/>'
                body +='<b>The Insurance Policy is due for renewal on: %s <br/>for employee: %s <br/>Employee id is %s <br/>Insurance Policy Number: %s <br/> Expires on: %s' % (rec.renewal_date,rec.name,rec.work_email,rec.policy_number,before_7days)
            body += '<br/>'
            body += '<br/>'
            body += 'Thank you,</b><br/>This is a system generated email do not reply.' 
            mail_ids = []
            for res in rec.work_email:
                mail_ids.append(mail_mail.create(cr, uid, {
                                'email_from': "demo.openerp.nitin@gmail.com",
                                'email_to':rec.work_email,
                                'subject': asunto,
                                'body_html': '<pre>%s</pre>' % body}, context=context))
                mail_mail.send(cr, uid, mail_ids, context=context)
    
