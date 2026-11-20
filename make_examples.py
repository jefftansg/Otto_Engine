"""Generate conspicuously fictional demonstration records for intake tests."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
root=Path(__file__).parent/'example_imports'/'smart_intake_demo'
root.mkdir(exist_ok=True,parents=True)
S=getSampleStyleSheet()
def make(name,entries):
    doc=SimpleDocTemplate(str(root/name),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=48,bottomMargin=50)
    flow=[Paragraph('<b>DEMONSTRATION ONLY - NOT AN OFFICIAL DOCUMENT</b>',S['Heading3']),Spacer(1,12)]
    for typ,val in entries:
        if typ=='p':flow.append(Paragraph(val,S['Normal']));flow.append(Spacer(1,8))
        elif typ=='h':flow.append(Paragraph(val,S['Heading2']));flow.append(Spacer(1,8))
        else:
            t=Table(val,colWidths=[65,165,100,76,79,83],hAlign='LEFT')
            t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            flow.append(t);flow.append(Spacer(1,9))
    doc.build(flow)
make('DEMO_ACRA_Profile_NOT_OFFICIAL.pdf',[
 ('h','ACRA Business Profile (Company) of MERIDIAN SERVICES PTE. LTD. (201688888A)'),
 ('p','Date of Incorporation: 07/10/2016'),
 ('p','Registered Office Address: 100 DEMONSTRATION ROAD #01-01 SINGAPORE 123456'),
 ('p','Principal Activity: Example consulting services'),
 ('p','Financial Year End: 31/12/2025'),
 ('p','This sample is fictional and not issued by the Accounting and Corporate Regulatory Authority.')
])
rows1=[['Date','Description','Reference','Deposit','Withdrawal','Balance'],
       ['02/01/2025','Customer payment','DEMO-001','1,000.00','','2,000.00'],
       ['07/05/2025','Office subscription','DEMO-002','','200.00','1,800.00']]
rows2=[['Date','Description','Reference','Deposit','Withdrawal','Balance'],
       ['12/07/2025','Customer payment','DEMO-003','300.00','','2,100.00'],
       ['30/11/2025','Bank charges','DEMO-004','','100.00','2,000.00']]
for filename,period,opening,closing,table in [
  ('DEMO_Bank_2025_H1.pdf','01/01/2025 to 30/06/2025','1,000.00','1,800.00',rows1),
  ('DEMO_Bank_2025_H2.pdf','01/07/2025 to 31/12/2025','1,800.00','2,000.00',rows2)]:
    make(filename,[('h','ILLUSTRATIVE OCBC Bank Statement'),('p','Account Number: 1234567890'),
      ('p','Statement Period: '+period),('p','Opening Balance: S$'+opening),('p','Closing Balance: S$'+closing),('t',table)])
print(root)
