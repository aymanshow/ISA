 
{
    'name':'ISA Recruitment',
    'version':'1.0',
    'category':'',
    'description':'Hr Recruitment Process',
    'author':'Drishti Tech',
    'website':'http://www.drishtitech.com',
    'depends':['base','base_status','decimal_precision','hr','survey','base_calendar','fetchmail','hr_recruitment','purchase','survey','hr_contract','hr_holidays','isa_hr_employee','isa_insurance','hr_attendance_payroll'],
    'data':[
            
#              'security/ir.model.access.csv',
#               'security/isa_security.xml',
            'wizard/hr_applicant_wizard_view.xml',
             'wizard/survey_wizard_view.xml',
             'wizard/mail_compose_message_view.xml',
             'isa_hr_applicant_view.xml',
             'isa_hr_view.xml', 
             'isa_hr_config_view.xml',
             'hr_job_view.xml',      
             'form_sequence.xml',
             'isa_survey_view.xml',  
             'hr_recruitment_menuitem.xml', 
             'form_sequence.xml',  
             'isa_survey_view.xml',
              'hr_recruitment_menuitem.xml',
             'employee_contract_view.xml',
             'demo_data.xml',
              ],
    'installable':True,
    'auto_install':False,
    'application':True,
           }  
    