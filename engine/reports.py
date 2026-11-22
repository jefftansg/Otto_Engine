"""PDF and XLSX reporting: no XBRL/statutory filing and no compliance certification."""
import io
import html
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, LongTable,
                                TableStyle, PageBreak, KeepTogether)
from .core import COA_MAP, money, money_str, balance_sheet_rows, profit_rows, trial_rows, director_balances

NAVY=colors.HexColor('#152641'); BLUE=colors.HexColor('#2C638A')
PALE=colors.HexColor('#EAF1F6'); GREY=colors.HexColor('#5C6977')
RED=colors.HexColor('#A33A3A')


def esc(s): return html.escape(str(s if s is not None else ''))


def _styles():
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SMETitle',fontName='Helvetica-Bold',fontSize=17,leading=22,textColor=NAVY,spaceAfter=8))
    styles.add(ParagraphStyle(name='SMESub',fontName='Helvetica',fontSize=10,leading=15,textColor=GREY,spaceAfter=10))
    styles.add(ParagraphStyle(name='SMEH2',fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=NAVY,spaceBefore=10,spaceAfter=7))
    styles.add(ParagraphStyle(name='SMEBody',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=8))
    styles.add(ParagraphStyle(name='SMETiny',fontName='Helvetica',fontSize=7.3,leading=10))
    styles.add(ParagraphStyle(name='SMETableHead',fontName='Helvetica-Bold',fontSize=7.4,leading=10,textColor=colors.white))
    styles.add(ParagraphStyle(name='SMEWarn',fontName='Helvetica-Bold',fontSize=8,leading=11,textColor=RED,spaceAfter=5))
    return styles


def _page(canvas,doc):
    canvas.saveState(); w,h=doc.pagesize
    canvas.setStrokeColor(colors.HexColor('#D7DFE5'))
    canvas.line(doc.leftMargin,h-17*mm,w-doc.rightMargin,h-17*mm)
    canvas.setFont('Helvetica',7); canvas.setFillColor(GREY)
    canvas.drawString(doc.leftMargin,11*mm,'Otto Financial Report Engine | DRAFT')
    canvas.drawRightString(w-doc.rightMargin,11*mm,f'Page {doc.page}')
    canvas.restoreState()


def _table(rows, widths, styles, wrap=None):
    wrap = set(wrap or [])
    vals=[]
    for idx,row in enumerate(rows):
        vals.append([Paragraph(esc(v).replace('\n','<br/>'),styles['SMETableHead' if idx==0 else 'SMETiny'])
                     if (idx==0 or c in wrap) else str(v) for c,v in enumerate(row)])
    t=LongTable(vals,colWidths=widths,repeatRows=1,hAlign='LEFT')
    commands=[('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8FB')]),
        ('LINEBELOW',(0,0),(-1,0),0.3,NAVY),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),5),
        ('RIGHTPADDING',(0,0),(-1,-1),5),('FONTSIZE',(0,1),(-1,-1),7.2),
        ('LINEBELOW',(0,-1),(-1,-1),0.2,colors.HexColor('#DBE2E8'))]
    t.setStyle(TableStyle(commands));return t


def _title(story,styles,text,subtitle=''):
    story.append(Paragraph(esc(text),styles['SMETitle']))
    if subtitle: story.append(Paragraph(esc(subtitle),styles['SMESub']))


def _paragraph(story, styles, body, style='SMEBody'):
    story.append(Paragraph(esc(body).replace('\n','<br/>'),styles[style]))


def _section(story, styles, title, rows, widths, wrap=None):
    story.append(Paragraph(esc(title),styles['SMEH2']))
    story.append(_table(rows,widths,styles,wrap))


def _status(result): return 'INCOMPLETE DRAFT - ERRORS PRESENT' if result['errors'] else 'DRAFT - DIRECTOR / ACCOUNTANT REVIEW REQUIRED'


def _header(story,styles,result,subject):
    c=result['config'];_title(story,styles,c.get('company_name',''),subject)
    _paragraph(story,styles,f"UEN: {c.get('uen','')}   |   Period: {result['start'].strftime('%d %B %Y')} - {result['end'].strftime('%d %B %Y')}   |   Currency: SGD")
    _paragraph(story,styles,_status(result),'SMEWarn')


def _validation(story,styles,result):
    _section(story,styles,'Validation results', [['Status','Finding']]+
      [['ERROR',v] for v in result['errors']]+[['REVIEW',v] for v in result['warnings']]
      if result['errors'] or result['warnings'] else [['Status','Finding'],['PASS','No internal validation messages. Professional review is still required.']],
      [21*mm,155*mm],wrap=[1])


def management_pdf(result):
    buf=io.BytesIO();w,h=landscape(A4)
    doc=SimpleDocTemplate(buf,pagesize=(w,h),leftMargin=15*mm,rightMargin=15*mm,
                          topMargin=23*mm,bottomMargin=19*mm, title='Draft Management Accounts')
    s=_styles();story=[];c=result['config'];p=result['package']
    inner=w-30*mm
    _header(story,s,result,'MANAGEMENT ACCOUNTS | Internal draft reporting package')
    rows=[['Item','SGD'],['Total assets',money_str(result['assets'])],
          ['Total liabilities',money_str(result['liabilities'])],['Total equity including current profit',money_str(result['equity'])],
          ['Revenue',money_str(result['revenue'])],['Expenses',money_str(result['expenses'])],
          ['Profit / (loss)',money_str(result['profit'])],['Bank balance',money_str(result['ledger_end'])]]
    _section(story,s,'Financial summary',rows,[inner*.72,inner*.28])
    _paragraph(story,s,'Generated from journal entries and reviewable source schedules; this is not an audit, compilation engagement or ACRA filing.')
    story.append(PageBreak())
    _header(story,s,result,'1. Balance Sheet')
    for typ in ('Asset','Liability','Equity'):
        filtered=[[code,name,amt] for code,name,amt in balance_sheet_rows(result) if code and result.get('coa', COA_MAP)[code]['type']==typ]
        if typ=='Equity':
            filtered.extend([[code,name,amt] for code,name,amt in balance_sheet_rows(result) if not code])
        _section(story,s,typ.upper(),[['Code','Account','SGD']]+(filtered or [['','No balance','-']]),[22*mm,inner-60*mm,38*mm],wrap=[1])
    _section(story,s,'Balance sheet check',[['Metric','SGD'],['Assets',money_str(result['assets'])],
        ['Liabilities + equity',money_str(result['liabilities']+result['equity'])],
        ['Difference',money_str(result['assets']-result['liabilities']-result['equity'])]],
        [inner-38*mm,38*mm])
    story.append(PageBreak())
    _header(story,s,result,'2. Profit and Loss')
    _section(story,s,'Period performance',[['Code','Account','SGD']]+profit_rows(result)+
        [['','Total revenue',money_str(result['revenue'])],['','Total expenses',money_str(result['expenses'])],
         ['','Profit / (loss) before additional adjustments',money_str(result['profit'])]],
        [22*mm,inner-60*mm,38*mm],wrap=[1])
    story.append(PageBreak())
    _header(story,s,result,'3. Trial Balance')
    _section(story,s,'All periods to financial year end',[['Code','Account','Debit SGD','Credit SGD']]+trial_rows(result),
             [20*mm,inner-90*mm,35*mm,35*mm],wrap=[1])
    story.append(PageBreak())
    _header(story,s,result,'4. Notes to Management Accounts')
    for title,body in [
        ('Basis of preparation', f"Draft prepared using the {c.get('reporting_framework','')} classification selected by management. Reporting framework eligibility and recognition/disclosure requirements require confirmation."),
        ('Transactions and supporting evidence','Bank feeds, personally funded director expenses, manual journals and invoice registers are separate inputs. All source records should be retained.'),
        ('Revenue recognition',c.get('revenue_policy','Not supplied; management to assess recognition timing and any deferred income.')),
        ('Director-funded expenses', 'Expense claims debit an expense or asset and credit the nominated director liability. Capital contributions require a separate, supported journal.'),
        ('Income taxes','No tax calculation is performed. Any tax expense, accrual and deferred tax adjustments require separately supported journals.'),
        ('Financial statement completeness','Depreciation, accruals, prepayments, liabilities, grants, related parties, impairment, contingencies and comparative data require manual assessment.'),
    ]:
        story.append(Paragraph(esc(title),s['SMEH2']));_paragraph(story,s,body)
    story.append(PageBreak())
    _header(story,s,result,'5. General Ledger')
    gl=[['Date','Journal','Account','Description','Debit','Credit','Evidence']]
    for e in result['entries']:
        gl.append([e['date'].isoformat(),e['journal_id'],e['account_code']+' '+result.get('coa', COA_MAP)[e['account_code']]['name'],
                   e['description'] or '',money_str(e['debit']),money_str(e['credit']),e['evidence_ref']])
    _section(story,s,'Posted journal lines',gl,[23*mm,24*mm,47*mm,75*mm,25*mm,25*mm,inner-219*mm],wrap=[2,3,6])
    story.append(PageBreak())
    _header(story,s,result,'6. Accounts Receivable Ageing')
    arr=[['Invoice','Customer','Due date','Bucket','Outstanding SGD']]
    for r in result['receivables']:
        arr.append([r['invoice_no'],r['customer'],r['due_date'].isoformat(),r['bucket'],money_str(r['outstanding'])])
    if len(arr)==1:arr.append(['-','No open invoices in supplied register','-','-', '0.00'])
    _section(story,s,'Outstanding invoices at year end',arr,[35*mm,inner-137*mm,31*mm,34*mm,37*mm],wrap=[1])
    story.append(PageBreak())
    _header(story,s,result,'7. Bank Reconciliation')
    opening_missing = result.get('bank_open_missing', False)
    closing_missing = result.get('bank_close_missing', False)
    statement_opening = 'Not provided' if opening_missing else money_str(result['bank_open'])
    statement_closing = 'Not provided' if closing_missing else money_str(result['bank_close'])
    expected_closing = (
        'Not available' if opening_missing
        else money_str(result['bank_open'] + result['bank_delta'])
    )
    statement_difference = (
        'Not available' if closing_missing
        else money_str(result['bank_close'] - result['ledger_end'])
    )
    _section(story,s,'Statement-to-ledger reconciliation',[['Item','SGD'],
            ['Statement beginning balance', statement_opening],
            ['Imported bank deposits less withdrawals',money_str(result['bank_delta'])],
            ['Expected bank statement closing', expected_closing],
            ['Statement closing balance entered', statement_closing],
            ['General ledger bank balance',money_str(result['ledger_end'])],
            ['Statement minus ledger difference', statement_difference]],
             [inner-46*mm,46*mm])
    if result.get('multi_bank'):
        rows=[['Bank code / name','Opening statement','Bank movement','Closing statement','Ledger closing','Difference']]
        for bank in result['bank_reconciliations']:
            rows.append([bank['code']+' '+bank['name']]+[money_str(bank[k]) if bank[k] is not None else 'Not provided' for k in ('opening','movement','closing','ledger_close','difference')])
        _section(story,s,'Individual account reconciliations',rows,[inner-150*mm]+[30*mm]*5,wrap=[0])
    _paragraph(story,s,'Unpresented cheques, deposits in transit, unrecorded charges and bank feeds not covering the full reporting period require separate review.')
    story.append(PageBreak())
    _header(story,s,result,'8. Source Bank Transactions')
    bankrows=[['Date','Reference','Description','Deposits','Withdrawals','Account','Evidence']]
    for r in p.bank:
        reference=r.get('reference','')
        if result.get('multi_bank'):
            reference=r.get('bank_account_code','')+' / '+reference
            if r.get('transfer_id'): reference+=' / '+r['transfer_id']
        bankrows.append([r.get('date',''),reference,r.get('description',''),r.get('deposit',''),r.get('withdrawal',''),r.get('account_code',''),r.get('evidence_ref','')])
    _section(story,s,'As imported / reviewed',bankrows,[24*mm,39*mm,73*mm,31*mm,31*mm,24*mm,inner-222*mm],wrap=[2,6])
    story.append(PageBreak())
    _header(story,s,result,'9. Director-Funded Expenses')
    cr=[['Date','Director','Merchant / description','Amount','Expense account','Evidence']]
    for r in p.claims:cr.append([r.get('date',''),r.get('director',''),(r.get('merchant','')+' / '+r.get('description','')).strip(' /'),r.get('amount',''),r.get('expense_account',''),r.get('evidence_ref','')])
    if len(cr)==1:cr.append(['-','-','No expense claims','0.00','-','-'])
    _section(story,s,'Claims funded personally',cr,[24*mm,44*mm,inner-167*mm,29*mm,28*mm,42*mm],wrap=[1,2,5])
    _section(story,s,'Director loan balances',[['Director','Code','Amount payable SGD']]+
             [[nm,code,money_str(amt)] for nm,code,amt in director_balances(result)],
             [inner-85*mm,35*mm,50*mm],wrap=[0])
    story.append(PageBreak())
    _header(story,s,result,'10. Supporting-Evidence Schedule')
    ev=[['Reference','Type','Source file','Review status','Remarks']]
    for r in p.evidence:
        ev.append([r.get('evidence_ref',''),r.get('document_type',''),r.get('source_file',''),r.get('review_status',''),r.get('remarks','')])
    if len(ev)==1:ev.append(['-','-','No register provided','-','-'])
    _section(story,s,'Evidence register',ev,[35*mm,36*mm,78*mm,31*mm,inner-180*mm],wrap=[1,2,4])
    story.append(PageBreak())
    _header(story,s,result,'11. Validation & Review Register')
    _section(story,s,'Validation results', [['Status','Finding']]+
      [['ERROR',v] for v in result['errors']]+[['REVIEW',v] for v in result['warnings']]
      if result['errors'] or result['warnings'] else [['Status','Finding'],['PASS','No internal validation messages. Director review remains required.']],
      [25*mm,inner-25*mm],wrap=[1])
    doc.build(story,onFirstPage=_page,onLaterPages=_page)
    return buf.getvalue()


def financial_statements_pdf(result):
    buf=io.BytesIO();w,h=A4
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=19*mm,rightMargin=19*mm,
                         topMargin=23*mm,bottomMargin=20*mm,title='Unaudited Financial Statements - Draft')
    s=_styles();story=[];c=result['config'];inner=w-38*mm
    _header(story,s,result,'UNAUDITED FINANCIAL STATEMENTS | PREPARATION DRAFT')
    _paragraph(story,s,'This document is a preparation draft derived from supplied bookkeeping records. It is NOT yet a director-approved, fully disclosed or certified set of financial statements. Financial reporting framework eligibility, recognition, accounting policies, disclosures, going concern, tax treatment and audit exemption must be independently reviewed.')
    story.append(Spacer(1,5*mm))
    story.append(Paragraph('Directors\' statement - draft for review',s['SMEH2']))
    _paragraph(story,s,'The directors must independently review the accounting records and these draft statements before deciding whether they present a true and fair view in accordance with the applicable Singapore financial reporting framework and Companies Act requirements.')
    _paragraph(story,s,'No representation regarding audit exemption, solvency, ability to pay debts, absence of contingent liabilities or directors\' interests has been automatically asserted by this engine.')
    _paragraph(story,s,'The director(s) named below may complete an appropriately verified directors\' statement after review and approval:')
    for d in c.get('directors',[]):
        _paragraph(story,s,f"Signature: ___________________________    {d.get('name','')}    Date: _________________")
    _paragraph(story,s,'Board approval date: ____________________')
    story.append(PageBreak())
    _header(story,s,result,'Statement of Financial Position')
    _paragraph(story,s,f"As at {result['end'].strftime('%d %B %Y')}")
    bs=[['Description','SGD']]
    for grp in ('Asset','Liability','Equity'):
        bs.append([grp.upper(),''])
        for code,v in sorted(result['balances'].items()):
            if result.get('coa', COA_MAP)[code]['type']==grp and v:
                bs.append(['    '+result.get('coa', COA_MAP)[code]['name'],money_str(v if grp=='Asset' else -v)])
        if grp=='Asset':bs.append(['TOTAL ASSETS',money_str(result['assets'])])
        if grp=='Liability':bs.append(['TOTAL LIABILITIES',money_str(result['liabilities'])])
        if grp=='Equity':
            if result['opening_profit']:bs.append(['    Prior-period earnings not closed to equity',money_str(result['opening_profit'])])
            bs.append(['    Current-year profit / (loss)',money_str(result['profit'])])
            bs.append(['TOTAL EQUITY',money_str(result['equity'])])
    bs.append(['TOTAL LIABILITIES AND EQUITY',money_str(result['liabilities']+result['equity'])])
    story.append(_table(bs,[inner-40*mm,40*mm],s,wrap=[0]))
    story.append(Spacer(1,7*mm))
    story.append(Paragraph('Statement of Comprehensive Income',s['SMEH2']))
    pl=[['Description','SGD']]
    for code,name,amount in profit_rows(result): pl.append([name,amount])
    pl.extend([['Total income',money_str(result['revenue'])],['Total expenses',money_str(result['expenses'])],
               ['Profit / (loss) for the year',money_str(result['profit'])]])
    story.append(_table(pl,[inner-40*mm,40*mm],s,wrap=[0]))
    story.append(PageBreak())
    _header(story,s,result,'Statement of Changes in Equity')
    _paragraph(story,s,'For the financial year ended '+result['end'].strftime('%d %B %Y'))
    eq_prior=-result['opening'].get('3100',Decimal(0))-result['opening'].get('3300',Decimal(0))+result['opening_profit']
    eq_share_change=-(result['period'].get('3100',Decimal(0))+result['period'].get('3300',Decimal(0)))
    _section(story,s,'Equity movement',[['Movement','SGD'],
        ['Opening equity (including prior-period profit/loss)',money_str(eq_prior)],
        ['Share capital / retained earnings postings in current period',money_str(eq_share_change)],
        ['Profit / (loss) for the current year',money_str(result['profit'])],
        ['Closing equity',money_str(result['equity'])]], [inner-42*mm,42*mm],wrap=[0])
    story.append(Paragraph('Statement of Cash Flows (direct-method working draft)',s['SMEH2']))
    _paragraph(story,s,'Derived from the cash-account journals and mapped counter-accounts. Confirm classification and adjust for bank transfers or other exceptional entries before issue.')
    _section(story,s,'Cash flow summary',[['Cash flow activity','SGD'],
        ['Net cash from operating activities',money_str(result['cashflows'].get('Operating',0))],
        ['Net cash from investing activities',money_str(result['cashflows'].get('Investing',0))],
        ['Net cash from financing activities',money_str(result['cashflows'].get('Financing',0))],
        ['Unallocated / review required',money_str(result['cashflows'].get('Unallocated',0))],
        ['Opening cash at bank',money_str(result['ledger_open'])],
        ['Closing cash at bank',money_str(result['ledger_end'])]],[inner-42*mm,42*mm],wrap=[0])
    story.append(PageBreak())
    _header(story,s,result,'Notes to the Financial Statements - DRAFT')
    closing_input = (
        'not provided' if result.get('bank_close_missing')
        else f"SGD {money_str(result['bank_close'])}"
    )
    notes=[
      ('1. Corporate information',f"{c.get('company_name','')}, UEN {c.get('uen','')}, is recorded as a {c.get('entity_type','')}. Registered office: {c.get('registered_address') or '[not supplied]'}. Activity: {c.get('principal_activity') or '[not supplied]'} ."),
      ('2. Basis of preparation',f"Management selected {c.get('reporting_framework','')} for this preparation draft. Eligibility, consistency of accounting policies and all mandatory disclosures require review. Figures are stated in SGD."),
      ('3. Significant accounting policies',c.get('accounting_policies') or 'ACCOUNTING POLICIES NOT PROVIDED. Review revenue recognition, expenses, estimates, receivables, depreciation, capitalisation and related-party balances.'),
      ('4. Revenue and expenses',f"Revenue and other income total SGD {money_str(result['revenue'])}; recognised expenses total SGD {money_str(result['expenses'])}. Detailed ledger and supporting records form part of the Management Accounts."),
      ('5. Cash and bank balances',f"Closing bank ledger balance is SGD {money_str(result['ledger_end'])}. Bank statement closing input is {closing_input}."),
      ('6. Trade receivables',f"Trade receivables per ledger are SGD {money_str(result['balances'].get('1100',0))}; unpaid invoices in the supplied AR schedule total SGD {money_str(sum((r['outstanding'] for r in result['receivables']),Decimal(0)))}."),
      ('7. Related parties - directors', '; '.join(f'{n}: SGD {money_str(v)}' for n,code,v in director_balances(result)) or 'No director loan register configured.'),
      ('8. Going concern',c.get('going_concern_note') or 'NOT CONFIRMED. Management must document its going-concern assessment before release.'),
      ('9. Income taxes','Tax computation and deferred-tax assessment are excluded from this system. Review whether additional journals and disclosures are required.'),
      ('10. Comparatives, commitments and contingencies',c.get('other_disclosures') or 'Comparative amounts, commitments, subsequent events, contingencies, directors\' interests and audit exemption have not been verified or automatically disclosed.'),
      ('11. Responsibilities','The company and its directors remain responsible for records, judgments, completeness, statutory financial reporting and approvals. No ACRA certification or XBRL submission is provided.'),
    ]
    for title,body in notes:
        story.append(Paragraph(esc(title),s['SMEH2']));_paragraph(story,s,body)
    story.append(PageBreak())
    _header(story,s,result,'Preparation Validation and Outstanding Review')
    _section(story,s,'Review register',[['Status','Finding']]+
        [['ERROR',v] for v in result['errors']]+[['REVIEW',v] for v in result['warnings']] or [['PASS','No automated validation messages.']],
        [23*mm,inner-23*mm],wrap=[1])
    doc.build(story,onFirstPage=_page,onLaterPages=_page)
    return buf.getvalue()


def xlsx_report(result):
    import xlsxwriter
    buf=io.BytesIO(); workbook=xlsxwriter.Workbook(buf,{'in_memory':True})
    fmt_title=workbook.add_format({'bold':True,'font_size':15,'font_color':'#152641'})
    fmt_head=workbook.add_format({'bold':True,'font_color':'white','bg_color':'#152641','bottom':1,'bottom_color':'#80A0B6'})
    fmt_num=workbook.add_format({'num_format':'#,##0.00;[Red](#,##0.00);-'})
    fmt_warn=workbook.add_format({'font_color':'#B23B3B','text_wrap':True})
    def sheet(name,rows,widths=None):
        ws=workbook.add_worksheet(name[:31]);ws.freeze_panes(1,0);ws.set_tab_color('#2C638A')
        if widths:
            for i,w in enumerate(widths):ws.set_column(i,i,w)
        for idx,row in enumerate(rows):
            for col,value in enumerate(row):
                if isinstance(value,Decimal):ws.write_number(idx,col,float(value),fmt_num)
                elif isinstance(value,(date,)):ws.write_string(idx,col,value.isoformat(),fmt_head if idx==0 else None)
                else:ws.write_string(idx,col,str(value) if value is not None else '',fmt_head if idx==0 else None)
        if rows:ws.autofilter(0,0,max(0,len(rows)-1),max(0,len(rows[0])-1))
        return ws
    c=result['config'];p=result['package']
    sheet('Overview',[['Metric','Value'],['Company',c.get('company_name','')],['UEN',c.get('uen','')],
         ['Start',c.get('fy_start','')],['End',c.get('fy_end','')],['Framework selected',c.get('reporting_framework','')],
         ['Status',_status(result)],['Total assets',result['assets']],['Total liabilities',result['liabilities']],
         ['Total equity',result['equity']],['Revenue',result['revenue']],['Expenses',result['expenses']],
         ['Profit / loss',result['profit']],['Bank closing',result['ledger_end']]], [32,62])
    sheet('Chart of Accounts',[['Code','Name','Account type','Presentation group','Cash flow class']]+
          [[c,a['name'],a['type'],a['group'],a['cashflow']] for c,a in sorted(result.get('coa', COA_MAP).items())],[14,49,22,30,22])
    tb_rows=[['Code','Account','Debit','Credit']]+[
        [code,result.get('coa', COA_MAP)[code]['name'],max(v,Decimal(0)),max(-v,Decimal(0))]
        for code,v in sorted(result['balances'].items()) if v]+[
        ['','TOTAL',result['trial_debit'],result['trial_credit']]]
    tb=sheet('Trial Balance',tb_rows,[14,50,22,22])
    tb.write_formula(len(tb_rows)-1,2,f'=SUM(C2:C{len(tb_rows)-1})',fmt_num,float(result['trial_debit']))
    tb.write_formula(len(tb_rows)-1,3,f'=SUM(D2:D{len(tb_rows)-1})',fmt_num,float(result['trial_credit']))
    bs=sheet('Balance Sheet',[['Code','Account','Amount SGD']]+
        [[code,name,money(amt)] for code,name,amt in balance_sheet_rows(result)]+
        [['','Total assets',result['assets']],['','Total liabilities',result['liabilities']],
         ['','Total equity',result['equity']]], [14,55,24])
    pl=sheet('Profit and Loss',[['Code','Account','Amount SGD']]+
        [[code,name,money(amt)] for code,name,amt in profit_rows(result)]+
        [['','Revenue',result['revenue']],['','Expenses',result['expenses']],['','Profit / loss',result['profit']]], [14,55,24])
    sheet('General Ledger',[['Date','Journal ID','Account code','Description','Debit','Credit','Source','Evidence ref']]+
        [[e['date'],e['journal_id'],e['account_code'],e['description'],e['debit'],e['credit'],e['source'],e['evidence_ref']] for e in result['entries']],[16,20,16,70,22,22,20,25])
    opening = 'Not provided' if result.get('bank_open_missing') else result['bank_open']
    closing_missing = result.get('bank_close_missing', False)
    closing = 'Not provided' if closing_missing else result['bank_close']
    br = sheet('Bank Reconciliation', [
        ['Item', 'SGD'],
        ['Statement opening', opening],
        ['Imported bank movement', result['bank_delta']],
        ['Statement closing', closing],
        ['Bank general ledger closing', result['ledger_end']],
        ['Difference'],
    ], [49, 25])
    if not closing_missing:
        difference = result['bank_close'] - result['ledger_end']
        br.write_formula('B6', '=B4-B5', fmt_num, float(difference))
    if result.get('multi_bank'):
        sheet('Bank Accounts',[['Code','Name','Opening statement','Movement','Closing statement','Opening ledger','Closing ledger','Difference']]+
            [[b['code'],b['name']]+[b[k] if b[k] is not None else 'Not provided' for k in ('opening','movement','closing','ledger_open','ledger_close','difference')] for b in result['bank_reconciliations']], [14,40,22,22,22,22,22,22])
    cf=sheet('Cash Flows',[['Classification','SGD']]+[[key,result['cashflows'].get(key,0)]
        for key in ('Operating','Investing','Financing','Unallocated')]+
        [['Opening bank',result['ledger_open']],['Closing bank',result['ledger_end']]], [40,24])
    cf.write_formula('B7','=B6+SUM(B2:B5)',fmt_num,float(result['ledger_end']))
    sheet('Director Balances',[['Director','Loan account','Balance payable']]+
        [[nm,code,amt] for nm,code,amt in director_balances(result)],[42,23,28])
    sheet('AR Ageing',[['Invoice','Customer','Due date','Age bucket','Outstanding']]+
        [[r['invoice_no'],r['customer'],r['due_date'],r['bucket'],r['outstanding']] for r in result['receivables']], [24,45,20,20,25])
    def safe_numeric(value):
        try:return money(value)
        except ValueError:return str(value)  # Preserve uncorrected source text for audit review.
    def sources(name,rows,cols,widths,numeric=()):
        material=[]
        for r in rows:
            material.append([safe_numeric(r.get(c,'')) if c in numeric else r.get(c,'') for c in cols])
        sheet(name,[cols]+material,widths)
    bankcols=['date','description','reference','deposit','withdrawal','account_code','evidence_ref','notes']
    bankwidths=[17,64,30,20,20,18,24,40]
    if result.get('multi_bank'):
        bankcols+=['bank_account_code','transfer_id']; bankwidths += [22,26]
    sources('Source Bank',p.bank,bankcols,bankwidths,numeric=('deposit','withdrawal'))
    sources('Source Claims',p.claims,['claim_id','date','director','merchant','description','amount','expense_account','evidence_ref','notes'],[20,17,32,38,60,20,20,25,35],numeric=('amount',))
    sources('Source Journals',p.journals,['journal_id','date','account_code','debit','credit','description','evidence_ref'],[22,17,17,20,20,70,30],numeric=('debit','credit'))
    sources('Evidence Register',p.evidence,['evidence_ref','document_type','source_file','remarks','review_status'],[26,28,66,52,20])
    sources('Source Invoices',p.invoices,['invoice_no','date','due_date','customer','amount','amount_paid','evidence_ref'],[22,20,20,50,22,22,28])
    sheet('Validation',[['Severity','Message']]+[['ERROR',v] for v in result['errors']]+
        [['REVIEW',v] for v in result['warnings']],[18,120])
    workbook.set_properties({'title':'Otto Draft Management Accounts','subject':'Local financial reporting workpapers',
      'comments':'Draft only. Not an ACRA filing or SFRS compliance certification.'})
    workbook.close()
    return buf.getvalue()
