from osv import fields, osv
import datetime
from datetime import datetime, timedelta
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from email_template import email_template


class certification_form(osv.osv):
    _name = "certification.form"
    _description = "Certification Form"
    
    _columns = {
        'supplier_id': fields.many2one('res.partner','Supplier', select=True),
        'product_id':fields.many2one('product.product','Certification Product',required=True),
        'certification_date':fields.date('Certification Date',required=True),
        'expiration_date':fields.date('Expiration Date',required=True),
        'employee_id':fields.many2one('hr.employee','User',readonly=True),
        'user_ids':fields.many2many('res.users','certi_user_rel_id','certi_id','user_id','Notification to be sent to'),
        }
    _defaults = {
        'certification_date': fields.date.context_today,
        }
    def default_get(self, cr, uid, fields, context=None):
        res = super(certification_form, self).default_get(cr, uid, fields, context=context)
        emp_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not emp_id:
            raise osv.except_osv(_('Error!'), _('First create user as Employee!'))
        emp_obj = self.pool.get('hr.employee').browse(cr, uid, emp_id[0], context=context)
        res.update({'employee_id': emp_id[0],
                    })
        return res
    
    
    def check_expiration_date(self, cr, uid, ids=False, context=None):
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        cur_date = date.today() + relativedelta( days = +30 )
        cur_date=str(cur_date)
        cur_date1 = date.today() + relativedelta( days = +7 )
        before_7days=str(cur_date1)
        ids = self.search(cr,uid,['|',('expiration_date','=',cur_date),('expiration_date','=',before_7days)])
        certi_obj=self.browse(cr,uid,ids)
        for rec in certi_obj:
            mail_mail = self.pool.get('mail.mail')
            if rec.expiration_date == cur_date:
                asunto = 'One month left for expiration of license of product %s with supplier %s' % (rec.product_id.name,rec.supplier_id.name)
                body = '' 
                body += '<b>Dear User,' 
                body += '<br/>'
                body += '<br/>'
                body +='<b>This is your first reminder for license certificate renewal for: <br/> Product: %s <br/> Supplier: %s <br/> Expires on: %s' % (rec.product_id.name,rec.supplier_id.name,cur_date)
            if rec.expiration_date == before_7days:
                asunto = 'One week left for expiration of license of product %s with supplier %s' % (rec.product_id.name,rec.supplier_id.name)
                body = '' 
                body += '<b>Dear User,'
                body += '<br/>'
                body += '<br/>'
                body +='<b>This is your last reminder for license certificate renewal for: <br/> Product: %s <br/> Supplier: %s <br/> Expires on: %s' % (rec.product_id.name,rec.supplier_id.name,before_7days)
            body += '<br/>'
            body += '<br/>'
            body += 'Thank you,</b><br/>This is a system generated email do not reply.' 
            mail_ids = []
            print"---",body
            for res in rec.user_ids:
                mail_ids.append(mail_mail.create(cr, uid, {
                                'email_from': "dhawalsharma786@gmail.com",
                                'email_to': res.email,
                                'subject': asunto,
                                'body_html': '<pre>%s</pre>' % body}, context=context))
                mail_mail.send(cr, uid, mail_ids, context=context)
certification_form()
