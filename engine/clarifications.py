"""Context-sensitive client clarification questions for SME reporting.

Every prompt comes from observable workspace/document state. The PDF is only a
request for information, never a statement that items have been verified.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from decimal import Decimal
from hashlib import sha256
from html import escape
from io import BytesIO, StringIO
import csv
import re

OTHER_RECORDS = [
    ('director_expenses', 'Did a director or owner pay for any company expenses using personal money?', 'Provide an expense claim list and receipts, including who paid and when.'),
    ('receivables', 'Did any customers still owe the company money at year-end?', 'Provide outstanding invoices and amounts received after year-end.'),
    ('payables', 'Did the company still owe any supplier bills or expenses at year-end?', 'Provide unpaid invoices and a list of outstanding bills.'),
    ('loans', 'Was any money borrowed, lent, or repaid by directors or third parties?', 'Provide loan agreements, balances and details of transfers.'),
    ('other_assets', 'Did the company own equipment, inventory, deposits or prepaid expenses at year-end?', 'Provide relevant invoices, asset lists and deposit records.'),
    ('prior_year', 'Was the business already operating before this financial year?', 'Provide the previous financial statements or opening trial balance.'),
]


def _id(kind, source=''):
    return kind + '-' + sha256(str(source).encode('utf-8')).hexdigest()[:12]


def _mask(text):
    """Suppress long bank account numbers if surfaced in bank errors."""
    return re.sub(r'(?<!\d)\d{8,20}(?!\d)', lambda m: '…'+m.group(0)[-4:], str(text or ''))


def _one(qs, kind, title, why, action, *, priority='Normal', source='', section='Other records', audience='Client'):
    qs.append(dict(id=_id(kind,source), question=title, why=why, request=action,
                   priority=priority, source=_mask(source), section=section, audience=audience))


def build_questions(pkg, parsed=(), bank_batch=None):
    """Generate a deterministic, evidence-driven list of questions.

    ``parsed`` is a sequence of (document, acra_result, bank_result) and
    ``bank_batch`` is the output from guided._bank_batch. No AI fabrication.
    """
    cfg=pkg.config
    qs=[]
    profiles=[a for _,a,_ in parsed if a.get('detected') and a.get('fields')]
    banks=[b for _,_,b in parsed if b.get('detected')]

    if not cfg.get('company_name') or not cfg.get('uen'):
        _one(qs,'company-details','What is the full registered company name and UEN?',
             'The company identity has not been confirmed in the workspace.',
             'Supply a current ACRA Business Profile or confirm the exact name and UEN.',
             priority='Required',section='Company')
    if not profiles and not cfg.get('acra_source'):
        _one(qs,'acra-document','Can you provide the latest ACRA Business Profile?',
             'No readable ACRA profile has been identified. The engine cannot verify registered particulars from bank statements.',
             'Upload an ACRA Business Profile PDF; this is not a request for the company’s login.',section='Company')
    if cfg.get('entity_type')=='Private limited company':
        if not cfg.get('registered_address'):
            _one(qs,'registered-address','What is the company’s registered office address at the reporting date?',
                 'Financial statement notes need reliable company particulars.',
                 'Provide the ACRA registered address or the updated Business Profile.',section='Company')
        if not cfg.get('directors'):
            _one(qs,'directors','Who were the directors during the year and who will review the statements?',
                 'The directors’ statement cannot be completed without verifying director identities and appointments.',
                 'Provide names and, where relevant, appointment or resignation dates; add directors in Advanced Mode.',section='Company')
        _one(qs,'share-capital','What were the issued and paid-up share capital and shareholders at year-end?',
             'Bank deposits alone do not prove share capital or share ownership.',
             'Provide ACRA capital/shareholder particulars and any share allotment or transfer records.',section='Accounting')
        if not cfg.get('going_concern_note'):
            _one(qs,'going-concern','Can the company continue paying its debts as they fall due?',
                 'The going-concern basis requires a director assessment, especially if cash is tight or there are losses.',
                 'Provide a director assessment and any support commitments where relevant.',section='Accounting')
        if not cfg.get('other_disclosures'):
            _one(qs,'contingencies','Were there any guarantees, legal claims, major commitments or important events after year-end?',
                 'Some matters require disclosure even when no bank transaction was recorded.',
                 'Confirm Yes/No and describe any matters, related parties or changes needing disclosure.',section='Accounting')
    if not cfg.get('fy_confirmed'):
        _one(qs,'financial-year','What are the exact financial year start and end dates?',
             'Reporting dates must be confirmed; the ACRA profile may not show the correct current year-end.',
             'Provide the official FYE record, last annual return or director confirmation.',
             priority='Required',section='Company')
    if profiles and not any(a.get('fields',{}).get('fy_end') for a in profiles) and not cfg.get('fy_confirmed'):
        _one(qs,'fye-not-shown','Where is the company’s financial year-end recorded?',
             'The uploaded ACRA profile does not explicitly show an FYE.',
             'Provide the FYE confirmation or prior-year accounts.',section='Company')

    if not banks and not pkg.bank:
        _one(qs,'no-bank','Can you provide all business bank statements for the financial year?',
             'No bank statements or transaction entries have been identified.',
             'Provide every month for every business bank account, including opening and closing pages.',
             priority='Required',section='Bank')

    if bank_batch:
        balances=bank_batch.get('balances',{})
        if banks and not balances.get('ready'):
            for i,err in enumerate(dict.fromkeys(balances.get('errors') or [])):
                _one(qs,'statement-coverage','Can you supply or clarify the missing bank statement information?',
                     'The uploaded bank statements do not yet establish complete, consistent year coverage.',
                     'Check the statement periods and balances. Details: '+_mask(err),
                     priority='Required',source=err,section='Bank')
        if bank_batch.get('mismatches'):
            for msg in dict.fromkeys(bank_batch['mismatches']):
                _one(qs,'statement-mismatch','Why do the transaction totals not agree with this bank statement?',
                     'The extracted credits less debits differ from the opening-to-closing movement.',
                     'Provide a complete statement or bank CSV export and verify the affected rows. '+_mask(msg),
                     priority='Required',source=msg,section='Bank')
        if bank_batch.get('issues'):
            for msg in list(dict.fromkeys(bank_batch['issues'])):
                _one(qs,'transaction-extraction','Can you clarify the unreadable or incomplete statement entries?',
                     'The application cannot safely read every transaction from the uploaded file.',
                     'Please supply a bank-exported CSV or Excel file, or a clearer statement. '+_mask(msg),
                     source=msg,section='Bank')
        if bank_batch.get('duplicates') and not bank_batch.get('already_imported'):
            _one(qs,'duplicates','Are these repeated transactions duplicates or separate genuine payments?',
                 f"{len(bank_batch['duplicates'])} imported/proposed bank row(s) may repeat.",
                 'Confirm which records are duplicates; do not import both until checked.',
                 priority='Required',section='Bank')
        if bank_batch.get('outside'):
            _one(qs,'outside-year','Do these transactions belong to the stated financial year?',
                 f"{len(bank_batch['outside'])} proposed row(s) fall outside the confirmed period.",
                 'Verify the financial year dates and the dates on the source statements.',
                 priority='Required',section='Bank')

    bank_ids={(b.get('bank'), b.get('account_id')) for b in banks if b.get('account_id')}
    if len(bank_ids)>1:
        _one(qs,'multiple-bank-accounts','How many different business bank accounts were active this year?',
             'The uploaded documents appear to cover multiple accounts; this version has a single bank-ledger control.',
             'List all accounts and supply a separate statement set for each. Use a qualified reviewer to combine accounts.',
             priority='Required',section='Bank')
    if banks and not cfg.get('bank_balances_confirmed'):
        _one(qs,'confirm-balances','Can you confirm the opening and year-end bank balances?',
             'Extracted balances have not yet been approved against the original statements.',
             'Check and confirm both amounts in Step 3, or provide missing statement pages.',
             priority='Required',section='Bank')
    opening=cfg.get('bank_statement_opening')
    try: nonzero=Decimal(str(opening or '0'))!=0
    except Exception: nonzero=False
    if nonzero and not cfg.get('prior_year_opening_reviewed'):
        _one(qs,'opening-ledger','Can you provide last year’s closing accounts or opening trial balance?',
             'A non-zero opening bank balance does not identify the corresponding assets, liabilities and equity.',
             'Provide previous year financial statements, trial balance or opening balances confirmed by the director.',
             priority='Required',section='Accounting')

    missing=[]
    for i,row in enumerate(pkg.bank,1):
        code=str(row.get('account_code') or '9999').strip()
        if code in ('','9999'):
            missing.append((i,row))
    for i,row in missing:
        amt=row.get('deposit') or row.get('withdrawal') or 'Unknown'
        incoming=bool(str(row.get('deposit') or '').strip() not in ('','0','0.00'))
        description=_mask(str(row.get('description') or '')[:115])
        direction='money received' if incoming else 'money paid'
        src=f"{row.get('date')}|{row.get('reference')}|{amt}|{description}"
        _one(qs,'uncategorised','What was this '+direction+' for?',
             f"Transaction {i}: {row.get('date','date missing')} — {description or '(no description)'} — S${amt}.",
             'Explain whether it was a sale, refund, transfer, loan, owner funding or business expense; provide an invoice or receipt if available.',
             priority='Required',source=src,section='Transactions')
    replies=cfg.get('simple_questions',{})
    for key,question,evidence in OTHER_RECORDS:
        answer=replies.get(key,'Not sure')
        if answer=='Not sure':
            _one(qs,key+'-unknown',question,
                 'Bank statements cannot answer this reliably, and no confirmed answer is recorded.',
                 'Reply Yes or No. If Yes: '+evidence,section='Other records')
        elif answer=='Yes':
            _one(qs,key+'-documents','Can you provide documents for: '+question[0].lower()+question[1:],
                 'This was answered Yes, so supporting records or accounting adjustments may be required.',
                 evidence,priority='Required' if key in ('director_expenses','receivables','payables','loans','prior_year') else 'Normal',
                 section='Other records')
    # In saved workspaces the original uploaded documents may no longer exist;
    # questions derived from the accounting ledger and configuration still work.
    return sorted(qs,key=lambda q:(0 if q['priority']=='Required' else 1,
                                   ['Company','Bank','Transactions','Accounting','Other records'].index(q['section']),q['id']))


def outstanding(questions, responses):
    return [q for q in questions if responses.get(q['id'],{}).get('status') not in ('Answered','Not applicable')]


def response_rows(questions, responses, only_open=True):
    selected=outstanding(questions,responses) if only_open else list(questions)
    return [{'Priority':q['priority'],'Topic':q['section'],'Question':q['question'],
             'Why we ask':q['why'],'What to provide':q['request'],
             'Status':responses.get(q['id'],{}).get('status','Needs answer'),
             'Answer':responses.get(q['id'],{}).get('answer',''), 'Source':q['source']}
            for q in selected]


def questions_csv(questions,responses,only_open=True):
    output=StringIO(newline='')
    columns=['Priority','Topic','Question','Why we ask','What to provide','Status','Answer','Source']
    w=csv.DictWriter(output,fieldnames=columns); w.writeheader()
    w.writerows(response_rows(questions,responses,only_open))
    return output.getvalue().encode('utf-8-sig')


def questions_pdf(company, questions, responses, only_open=True):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    docbuf=BytesIO()
    pdf=SimpleDocTemplate(docbuf,pagesize=A4,leftMargin=19*mm,rightMargin=19*mm,
                          topMargin=16*mm,bottomMargin=18*mm,title='Client Information Request')
    base=getSampleStyleSheet()
    h=ParagraphStyle('QuestionTitle',parent=base['Heading3'],fontName='Helvetica-Bold',fontSize=10.3,leading=13.5,spaceAfter=4,textColor=colors.HexColor('#17365c'))
    p=ParagraphStyle('QuestionBody',parent=base['BodyText'],fontSize=9,leading=12,spaceAfter=5)
    sub=ParagraphStyle('QuestionSub',parent=p,textColor=colors.HexColor('#515e70'))
    title=ParagraphStyle('MainTitle',parent=base['Heading1'],fontSize=18,leading=23,textColor=colors.HexColor('#17365c'))
    story=[Paragraph('Information needed to prepare financial reports',title),
           Spacer(1,6),Paragraph(escape(company or 'Company not yet confirmed'),base['Heading3']),
           Paragraph('Please answer the following questions and attach documents where requested. '
                     'We will review your answers before preparing draft management accounts and financial statements.',p),Spacer(1,8)]
    selected=outstanding(questions,responses) if only_open else list(questions)
    if not selected:story.append(Paragraph('No clarification questions are currently outstanding.',p))
    for i,q in enumerate(selected,1):
        ans=responses.get(q['id'],{})
        blocks=[Paragraph(f'{i}. {escape(q["question"])}',h),
                Paragraph('<b>Reason:</b> '+escape(q['why']),sub),
                Paragraph('<b>Please provide:</b> '+escape(q['request']),p)]
        if not only_open:
            blocks.append(Paragraph('<b>Status:</b> '+escape(ans.get('status','Needs answer')),p))
        if ans.get('answer'):
            blocks.append(Paragraph('<b>Recorded response:</b> '+escape(ans['answer']),p))
        else:
            blocks.append(Paragraph('<b>Response:</b> ___________________________________________________',p))
        blocks.append(Spacer(1,9))
        story.append(KeepTogether(blocks))
    story.append(Spacer(1,8))
    story.append(Paragraph('Prepared for information collection only. This questionnaire is not an audit, '
                           'an ACRA filing or evidence of compliance with Singapore reporting standards.',sub))
    def footer(canvas,document):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#6b7280'))
        canvas.drawString(19*mm,12*mm,'Otto Financial Report Engine | Draft client clarification request')
        canvas.drawRightString(191*mm,12*mm,str(document.page));canvas.restoreState()
    pdf.build(story,onFirstPage=footer,onLaterPages=footer)
    return docbuf.getvalue()
