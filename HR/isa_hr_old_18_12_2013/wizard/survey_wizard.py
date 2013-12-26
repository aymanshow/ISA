from osv import fields,osv


class survey_create_wiz(osv.osv_memory):
    _name='survey.create.wiz'
    _columns={
              
              'survey_id':fields.many2one('survey','Survey Name'),
              'user_id':fields.many2one('res.users','User'),
              'date_deadline':fields.date('Date Deadline'),
              'response':fields.many2one('survey.response','Answer')
              }


    def create_test(self,cr,uid,ids,context=None):
        if ids:
            list=[]
            vals={}
            print "=====================ids=======================",ids,context['active_id']
            obj=self.browse(cr,uid,ids[0])
            print 'obj===============================wiz==',obj
            print obj.survey_id.id,'================='
            print obj.user_id.id,'====================='
            survey_id=obj.survey_id.id,
            print 'survey_id========================',survey_id
            vals={
                  'aplicant_id':context['active_id'],
                  'survey_id':obj.survey_id.id,
                  'user_id':obj.user_id.id,
                  'date_deadline':obj.date_deadline
                  }
            list.append(obj.user_id.id)
            test_id=self.pool.get('survey.test.line').create(cr,uid,vals)
            print "test_id===========================test_id",test_id,obj.survey_id.id,
            survey_obj=self.pool.get('survey').browse(cr,uid,obj.survey_id.id)
            print 'survey_obj.id========================================',survey_obj,
            print 'list',list
            self.pool.get('survey').write(cr,uid,survey_obj.id,{'invited_user_ids':[[6,0,list]]})
            return True
