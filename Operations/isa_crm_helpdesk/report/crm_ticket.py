import time
from report import report_sxw

class engineer_ticket(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(engineer_ticket, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time':time,
            })
       
report_sxw.report_sxw('report.engineer_ticket', 'crm.helpdesk', 'addons/isa_crm_helpdesk/report/crm_ticket_report.rml', parser=engineer_ticket,)
