import time
from report import report_sxw

class engineer_job_order(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(engineer_job_order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time':time,
            })
       
report_sxw.report_sxw('report.engineer_job_order', 'job.order1', 'addons/isa_crm_helpdesk/report/crm_job_order_report.rml', parser=engineer_job_order,)
