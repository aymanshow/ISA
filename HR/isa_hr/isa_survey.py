import base64
import datetime
from lxml import etree
import os
from time import strftime
from openerp import addons, netsvc, tools
from openerp.osv import fields, osv
import survey
from openerp.tools import to_xml
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval
import ast
class survey_question(osv.osv):
    _name='survey.question'
    _inherit = "survey.question"
    _columns={
              'correct_ans':fields.selection([('1','1'),('2','2'),('3','3'),('4','4')],'Correct Answer',required=True),
              'marks':fields.integer('Marks for this question', required=True),
              }

class survey(osv.osv):
    _name='survey'
    _inherit='survey'
    def _get_marks(self, cr, uid, ids, fld_name, arg, context=None):
        res={}
        for val in self.browse(cr,uid,ids):
            marks=0
            for line in val.page_ids:
                marks+=line.total_marks
            res[val.id]=marks
        return res
    _columns={
              'total_marks':fields.function(_get_marks,method=True,type='integer',string='Total Marks'),
            'type1':fields.selection([('1','Recruitment Test'),('2', 'Appraisal Survey'),('3', 'Other Process')], 'Survey Type')
              }
class survey_page(osv.osv):
    _name='survey.page'
    _inherit='survey.page'
    def _get_marks(self, cr, uid, ids, fld_name, arg, context=None):
        res={}
        for val in self.browse(cr,uid,ids):
            marks=0
            for line in val.question_ids:
                marks+=line.marks
            res[val.id]=marks
        return res
    _columns={
              'total_marks':fields.function(_get_marks,method=True,type='integer',string='Total Marks'),
              }

class survey_question_wiz(osv.osv_memory):
    _name = 'survey.question.wiz'
    _inherit='survey.question.wiz'
    def action_next(self, cr, uid, ids, context=None):
        """
        Goes to Next page.
        """
        if context is None:
            context = {}
        surv_name_wiz = self.pool.get('survey.name.wiz')
        search_obj = self.pool.get('ir.ui.view')
        search_id = search_obj.search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'transfer':True, 'page':'next'})
        rec = surv_name_wiz.browse(cr,uid,context.get('sur_name_id',False)).store_ans
        rec=ast.literal_eval(rec)
        marks=0
        ques_id=0
        key_id=0
        for key,val in rec.iteritems():
            for val1 in val.iteritems():
                if val1[0] == 'question_id':
                    ques_id=val1[1]
                else:
                    key_id=val1[1]
            if ques_id and key_id:
                obj = self.pool.get('survey.question').browse(cr,uid,int(ques_id))
                for val in obj.answer_choice_ids:
                    if str(obj.correct_ans)==str(val.sequence) and int(key_id) == val.id:
                          marks=marks+obj.marks
        survey_id = context.get('survey_id', False)
        self.write(cr,uid,ids[0],{'marks':marks})
        self.pool.get('survey').write(cr,uid,survey_id,{'marks':marks})
        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'survey.question.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'search_view_id': search_id[0],
            'context': context
        }
