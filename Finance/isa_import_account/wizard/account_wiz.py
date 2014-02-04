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
class import_account(osv.osv_memory):
    _name='import.account'
    _columns={
            'file':fields.binary("File Path:"),
            'file_name':fields.char('File Name:'),
              }
    def import_account_info(self,cr,uid,ids,context=None):
        cur_obj = self.browse(cr,uid,ids)[0]
        account_type_obj=self.pool.get('account.account.type')
        file_data=cur_obj.file
        val=base64.decodestring(file_data)
        fp = StringIO.StringIO()
        fp.write(val)     
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        sheet=wb.sheet_by_index(0)
        list=[]
        for i in range(1,sheet.nrows):
            
            
            
            account_code =sheet.row_values(i,0,sheet.ncols)[0]
            if type(account_code)==type(1.0):
                    account_code=str(int(account_code))
            if account_code:
                acc_id=self.pool.get('account.account').search(cr, uid, [('code','=',account_code)])
                account_name =sheet.row_values(i,0,sheet.ncols)[2]
                portuguese_name =sheet.row_values(i,0,sheet.ncols)[1]
                parent_id =sheet.row_values(i,0,sheet.ncols)[3]
                internal_type =sheet.row_values(i,0,sheet.ncols)[4]
                account_type=sheet.row_values(i,0,sheet.ncols)[5]
                if type(parent_id)==type(1.0):
                    parent_id=str(int(parent_id))
                if account_type:
                    acc_type=account_type_obj.search(cr, uid, [('name','=',account_type)], context=context)
                acc_parent_id=self.pool.get('account.account').search(cr, uid, [('code','=',parent_id)], context=context)
                if not acc_parent_id:
                    list.append(i)
                    
                if not acc_id:
                    demo=self.pool.get('account.account').create(cr,uid,{'code' : account_code,'name' : account_name,'portuguese_name':portuguese_name,'type':internal_type,'user_type':acc_type[0],'parent_id':acc_parent_id and acc_parent_id[0] or False}) 
                else:
                     self.pool.get('account.account').write(cr,uid,acc_id,{'code' : account_code,'name' : account_name,'portuguese_name':portuguese_name,'type':internal_type,'user_type':acc_type[0],'parent_id':acc_parent_id and acc_parent_id[0] or False})    
        
        return True
