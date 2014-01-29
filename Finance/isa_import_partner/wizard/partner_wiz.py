from osv import osv
from osv import fields
import datetime
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from tools.translate import _
import StringIO
import cStringIO
import base64
import xlrd
import string
class import_partner(osv.osv_memory):
    _name='import.partner'
    _columns={
            'file':fields.binary("File Path:"),
            'file_name':fields.char('File Name:'),
              }
    def import_partner_info(self,cr,uid,ids,context=None):
        cur_obj = self.browse(cr,uid,ids)[0]
        account_type_obj=self.pool.get('account.account.type')
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        for i in range(1,sheet.nrows):
            supplier=False
            customer=False
            account_code =sheet.row_values(i,0,sheet.ncols)[0]
            account_name =sheet.row_values(i,0,sheet.ncols)[1]
            
            acc_id=self.pool.get('account.account').search(cr, uid, [('name','=',account_name),('code','=',account_code)])
            name =sheet.row_values(i,0,sheet.ncols)[3]
            notification_email_send =sheet.row_values(i,0,sheet.ncols)[4]
            supp =sheet.row_values(i,0,sheet.ncols)[5]
            custo =sheet.row_values(i,0,sheet.ncols)[6]
            if str(supp)=='True':
                supplier=True
            if str(custo)=='True':
                customer=True
#                 if isinstance (acc_parent_id(list,tuple)):
#                     acc_parent_id=acc_parent_id[0]
            if acc_id:
                partner_id=self.pool.get('res.partner').search(cr,uid,[('name','=',name)])
                if not partner_id:
                    self.pool.get('res.partner').create(cr,uid,{'name' : name,'notification_email_send' : 'none','supplier':supplier,
                                                            'customer':customer,'property_account_payable':acc_id[0],'property_account_receivable':acc_id[0]}) 
                elif partner_id:
                    self.pool.get('res.partner').write(cr,uid,partner_id[0],{'name' : name,'notification_email_send' : 'none','supplier':supplier,
                                                            'customer':customer,'property_account_payable':acc_id[0],'property_account_receivable':acc_id[0]})
#             
#else:
#                 raise osv.except_osv(
#                     _('Warning!'),
#                     _('No Account Created For '))
        return True
