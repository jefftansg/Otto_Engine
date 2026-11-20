"""Fictional first-year files to test the Guided Mode workflow."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

root=Path(__file__).parent/'example_imports'/'guided_demo'
root.mkdir(exist_ok=True,parents=True)
styles=getSampleStyleSheet()
def make(name,blocks):
    d=SimpleDocTemplate(str(root/name),pagesize=A4,leftMargin=48,rightMargin=48)
    flow=[Paragraph('FICTIONAL SAMPLE ONLY - NOT A REAL ACRA OR BANK DOCUMENT',styles['Heading3']),Spacer(1,18)]
    for kind,payload in blocks:
        if kind=='h':flow.append(Paragraph(payload,styles['Heading2']))
        elif kind=='p':flow.append(Paragraph(payload,styles['Normal']))
        else:
            grid=Table(payload,colWidths=[59,150,75,71,71,70]);grid.setStyle(TableStyle([
                ('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
                ('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
            flow.append(grid)
        flow.append(Spacer(1,9))
    d.build(flow)
make('SAMPLE_ACRA_Not_Official.pdf',[
    ('h','ACRA Business Profile (Company) of GUIDED DEMO PTE. LTD. (202588888A)'),
    ('p','Date of Incorporation: 01/01/2025'),
    ('p','Registered Office Address: 1 SAMPLE STREET SINGAPORE 123456'),
    ('p','Principal Activity: Illustrative design and consulting services'),
    ('p','Financial Year End: 31/12/2025'),
    ('p','This fictional sample is not issued by ACRA.')])
rows=[['Date','Description','Reference','Deposit','Withdrawal','Balance'],
      ['01/01/2025','Share capital paid in','SAMPLE-S01','1,000.00','','1,000.00'],
      ['15/02/2025','Customer service payment','SAMPLE-S02','300.00','','1,300.00'],
      ['07/03/2025','Software subscription','SAMPLE-S03','','50.00','1,250.00'],
      ['22/12/2025','Bank service charge','SAMPLE-S04','','20.00','1,230.00']]
make('SAMPLE_BANK_Not_Official.pdf',[
    ('h','ILLUSTRATIVE OCBC Bank Statement'),
    ('p','Account Number: 1234567890'),
    ('p','Statement Period: 01/01/2025 to 31/12/2025'),
    ('p','Opening Balance: S$0.00'),
    ('p','Closing Balance: S$1,230.00'),
    ('t',rows),
])
print('Generated sample PDF files',root)
