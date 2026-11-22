"""Conservative local extraction of ACRA particulars and bank statement summaries.

Nothing is posted automatically; every proposed value records its provenance.
No ACRA data service, authentication or live financial data access is used.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from hashlib import sha256
import re
from .importers import parse_iso_date, parse_money, fields, guess_field, convert_records, existing_duplicates

DATE_RX = r'(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})'
AMOUNT_RX = r'(?:\(?-?\s*(?:S\$|SGD|\$)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\)?|\(?-?\s*(?:S\$|SGD|\$)?\s*\d+\.\d{2}\)?)'
UEN_RX = r'(?:\d{9}[A-Z]|[STFG]\d{2}[A-Z]{2}\d{4}[A-Z])'

def _lines(s):
    return [re.sub(r'\s+',' ',line).strip() for line in (s or '').splitlines() if line.strip()]

def _date(value):
    if not value:return None
    try:return parse_iso_date(value)
    except ValueError:return None

def _label_date(text, labels):
    for line in _lines(text):
        for label in labels:
            match = re.search(r'\b'+label+r'\b\s*[:\-]?\s*('+DATE_RX+r')\b',line,re.I)
            if match:
                d=_date(match.group(1))
                if d:return d
    return None

def _label_value(lines,rx,allow_next=True):
    for idx,line in enumerate(lines):
        m=re.search(rx,line,re.I)
        if m:
            value=line[m.end():].strip(' :\t-')
            if value:return value
            if allow_next and idx+1<len(lines):return lines[idx+1]
    return None

def extract_acra_profile(doc):
    """Extract only explicit ACRA business-profile fields; no guessed statutory information."""
    text=doc.text_excerpt or ''
    lines=_lines(text)
    if not (re.search(r'ACRA|ACCOUNTING AND CORPORATE REGULATORY AUTHORITY|BIZFILE|BUSINESS PROFILE',text,re.I)):
        return dict(detected=False,fields={},warnings=['No ACRA/Bizfile Business Profile heading detected.'])
    found={}; warnings=[]
    m=re.search(r'Business\s+Profile\s*\(\s*Company\s*\)\s*of\s+([\s\S]{1,180}?)\s*\(\s*('+UEN_RX+r')\s*\)',text,re.I)
    if m:
        found['company_name']=re.sub(r'\s+',' ',m.group(1).strip().upper());found['uen']=m.group(2).upper()
    else:
        name=_label_value(lines,r'^(?:Entity|Company|Business)\s+Name\s*[:\-]?')
        if name and len(name)<180: found['company_name']=name.strip()
        u=_label_value(lines,r'^(?:UEN|Registration\s+(?:No\.?|Number)|Unique\s+Entity\s+Number)\s*[:\-]?')
        if u:
            um=re.search(UEN_RX,u.upper())
            if um:found['uen']=um.group(0)
    # Restrict to known dates; do not treat annual-return dates as financial year-end.
    dates={
       'fy_end': [r'(?:Financial\s+Year\s+End(?:ing)?|FYE|Current\s+Financial\s+Year\s+End)'],
       'incorporation_date': [r'(?:Date\s+of\s+Incorporation|Incorporation\s+Date|Date\s+of\s+Registration)'],
    }
    for field,labels in dates.items():
        d=_label_date(text,labels)
        if d:found[field]=d
    act=_label_value(lines,r'^(?:Primary\s+Activity|Principal\s+(?:Activity|Business\s+Activity)|Primary\s+SSIC|Business\s+Activity)\s*[:\-]?')
    if act and len(act)<220: found['principal_activity']=act
    # Addresses are multiline; capture only clearly labelled address and stop at next field.
    for idx,line in enumerate(lines):
        z=re.match(r'^(?:Registered\s+Office\s+Address|Registered\s+Address|Address\s+of\s+Registered\s+Office)\s*[:\-]?\s*(.*)',line,re.I)
        if not z:continue
        parts=[z.group(1)] if z.group(1) else []
        for following in lines[idx+1:idx+5]:
            if re.search(r'^(?:Primary|Principal|Secondary|Business|Status|Registration|Date\s+of|Company\s+Type|Issued|Paid|Share|Officer|Director|Secretary|Telephone|Email|UEN|Financial|FYE|Postal)\b',following,re.I):break
            if re.search(r'^(?:\d{4}\b|Page\s+\d+\s+of)',following,re.I):break
            parts.append(following)
            if 'SINGAPORE' in following.upper() and re.search(r'\d{6}',following):break
        address=' '.join(x for x in parts if x).strip()
        if address and len(address)<=300:found['registered_address']=address
        break
    t=re.search(r'\b(?:EXEMPT\s+PRIVATE\s+COMPANY|PRIVATE\s+COMPANY\s+LIMITED\s+BY\s+SHARES|PRIVATE\s+LIMITED\s+COMPANY)\b',text,re.I)
    if t or re.search(r'PTE\.?\s+LTD\.?',found.get('company_name',''),re.I):
        found['entity_type']='Private limited company'
    if 'fy_end' not in found:
        warnings.append('Financial year-end not explicitly found. ACRA Business Profiles do not always provide the current FYE; obtain a dated ACRA FYE record, last annual return or director confirmation.')
    if 'registered_address' not in found:
        warnings.append('Registered address not confidently extracted; review it manually.')
    warnings.append('Extraction is not verification of the document’s authenticity or current ACRA status.')
    return dict(detected=bool(found),fields=found,warnings=warnings,source=doc.name,sha256=doc.sha256)

def _money_candidates(rest):
    # Avoid mistakenly collecting account numbers or dates as monetary amounts:
    # balances require cents, or a comma-separated integer.
    rx=r'(?<!\w)(?:S\$\s*|SGD\s*|\$\s*)?\(?-?\d{1,3}(?:,\d{3})+\.\d{2}\)?|(?<!\w)(?:S\$\s*|SGD\s*|\$\s*)?\(?-?\d+\.\d{2}\)?'
    result=[]
    for x in re.findall(rx,rest,re.I):
        try:result.append(parse_money(x))
        except ValueError:pass
    return result

def _label_balance(lines,patterns,prefer_last=False):
    vals=[]
    for i,line in enumerate(lines):
        for pattern in patterns:
            m=re.search(r'\b(?:'+pattern+r')\b\s*[:\-]?\s*',line,re.I)
            if m:
                amounts=_money_candidates(line[m.end():])
                if not amounts and i+1<len(lines):amounts=_money_candidates(lines[i+1])
                if len(amounts)==1:
                    vals.append((amounts[0],i,line))
                # If 2 or more, do not guess between Dr/Cr or amount/balance columns.
                break
    if not vals:return None,[]
    different={v[0] for v in vals}
    if len(different)>1:
        return None,[f'Conflicting labelled balance amounts detected ({len(different)} distinct values); check statement manually.']
    return vals[-1 if prefer_last else 0][0],[]

def _period(lines, ocbc_statement=False):
    joined='\n'.join(lines)
    patterns=[
      r'(?:Statement\s+Period|Period\s+Covered|For\s+the\s+Period|Period\s+From)\s*[:\-]?\s*('+DATE_RX+r')\s*(?:to|through|until|\-|–|—)\s*('+DATE_RX+r')',
      r'\bFrom\s+('+DATE_RX+r')\s+(?:to|through|until)\s+('+DATE_RX+r')',
    ]
    for pattern in patterns:
        m=re.search(pattern,joined,re.I)
        if m:
            a,b=_date(m.group(1)),_date(m.group(2))
            if a and b and a<=b:return a,b
    if ocbc_statement:
        # OCBC prints the period beside the account title, without "Period"/"From".
        # Match only a complete heading line, never dates buried in transaction text.
        periods=set()
        heading=r'^(?:BUSINESS\s+GROWTH\s+ACCOUNT\s+)?('+DATE_RX+r')\s+TO\s+('+DATE_RX+r')$'
        for line in lines:
            m=re.fullmatch(heading,line,re.I)
            if m:
                a,b=_date(m.group(1)),_date(m.group(2))
                if a and b and a<=b:periods.add((a,b))
        if len(periods)==1:return next(iter(periods))
    return None,None

def extract_bank_statement(doc):
    """Returns a reviewable proposal; never derives opening/closing from unrelated total columns."""
    lines=_lines(doc.text_excerpt)
    if not lines and doc.tables:
        lines=[ ' | '.join(row) for table in doc.tables for row in table.rows[:40]+table.rows[-15:]]
    # Some Excel and CSV statements carry metadata outside transaction table.
    if doc.tables:
        row_lines=[' '.join(row) for table in doc.tables for row in (table.rows[:35]+table.rows[-15:])]
        lines+=row_lines
    if not lines:return dict(detected=False,source=doc.name,warnings=['No readable statement text.'])
    text='\n'.join(lines)
    is_bank=bool(re.search(r'\b(?:BANK\s+STATEMENT|ACCOUNT\s+STATEMENT|TRANSACTION\s+HISTORY|STATEMENT\s+OF\s+ACCOUNT|BALANCE\s+BROUGHT\s+FORWARD)\b',text,re.I))
    op,op_err=_label_balance(lines,[r'Opening\s+(?:Ledger\s+)?Balance',r'Balance\s+Brought\s+Forward',r'Brought\s+Forward\s+Balance',r'Beginning\s+Balance',r'Balance\s+B\s*/\s*F'])
    cl,cl_err=_label_balance(lines,[r'Closing\s+(?:Ledger\s+)?Balance',r'Balance\s+Carried\s+Forward',r'Carried\s+Forward\s+Balance',r'Ending\s+Balance',r'Balance\s+C\s*/\s*F'],prefer_last=True)
    start,end=_period(lines, ocbc_statement=bool(is_bank and re.search(r'\bOCBC\b',text,re.I)))
    if op is not None or cl is not None:is_bank=True
    account=''
    for i,line in enumerate(lines[:80]):
        m=re.search(r'\b(?:Account\s+(?:Number|No\.?|#)|A/C\s+(?:Number|No\.?|#))\s*[:\-]?\s*([A-Z0-9-]{6,30})\b',line,re.I)
        if m:
            account=m.group(1);break
    account_id=sha256(account.upper().encode()).hexdigest()[:12] if account else ''
    masked=('••••'+re.sub(r'[^0-9A-Za-z]','',account)[-4:]) if account else 'Not identified'
    bank=''
    for b in ('OCBC','DBS','POSB','UOB','STANDARD CHARTERED','MAYBANK','CIMB','HSBC','RHB','BANK OF CHINA'):
        if re.search(r'\b'+re.escape(b)+r'\b',text[:2500],re.I):bank=b;break
    warnings=op_err+cl_err
    if op is None:warnings.append('No unambiguous labelled opening balance found.')
    if cl is None:warnings.append('No unambiguous labelled closing balance found.')
    if not(start and end):warnings.append('Statement period not confidently identified; financial-year coverage cannot yet be verified.')
    if not account_id:warnings.append('Bank account number not detected; verify that all statements relate to the same account.')
    if not is_bank:
        return dict(detected=False,source=doc.name,warnings=['Document is not identified as a bank statement.'])
    return dict(detected=True,source=doc.name,sha256=doc.sha256,bank=bank,account_id=account_id,
                masked_account=masked,period_start=start,period_end=end,
                opening=str(op) if op is not None else None,
                closing=str(cl) if cl is not None else None,warnings=warnings)

def suggested_start(fye,incorporation=''):
    """12-month heuristic ONLY; must be explicitly confirmed by the director."""
    end=date.fromisoformat(fye)
    prevyear=end.year-1
    prev=date(prevyear,end.month,min(end.day,monthrange(prevyear,end.month)[1]))
    start=prev+timedelta(days=1)
    if incorporation:
        try:
            inc=date.fromisoformat(incorporation)
            if start<inc<=end:start=inc
        except ValueError:pass
    return start.isoformat()

def consolidate_statement_balances(summaries,fy_start,fy_end):
    """Calculate bank opening/closing only for complete, contiguous single-account statements."""
    errors=[]
    valid=[x for x in summaries if x.get('detected')]
    if not valid:return dict(ready=False,errors=['No recognised bank statements.'],rows=[])
    accounts={x.get('account_id') for x in valid if x.get('account_id')}
    if len(accounts)>1:errors.append('Different bank accounts detected. V1.2 supports one account (1000) per workspace; do not mix statements.')
    if not all(x.get('account_id') for x in valid):errors.append('At least one statement has no identifiable account number; confirm account continuity manually.')
    sorted_rows=sorted(valid,key=lambda x:(x.get('period_start') or '',x.get('period_end') or '',x.get('source','')))
    if any(not x.get('period_start') or not x.get('period_end') for x in sorted_rows):errors.append('Some statement periods could not be identified; cannot verify complete coverage.')
    # Deduplicate repeat upload of the same statement by content hash.
    dedup={}
    for s in sorted_rows:dedup.setdefault(s.get('sha256') or s.get('source'),s)
    sorted_rows=list(dedup.values())
    for s in sorted_rows:
        if s.get('opening') is None or s.get('closing') is None:errors.append('Missing opening or closing balance: '+s['source'])
    try:
        start=date.fromisoformat(fy_start);end=date.fromisoformat(fy_end)
    except (ValueError,TypeError):return dict(ready=False,errors=['Confirm financial year dates before using extracted balances.'],rows=sorted_rows)
    if not errors:
        if date.fromisoformat(sorted_rows[0]['period_start'])>start or date.fromisoformat(sorted_rows[-1]['period_end'])<end:
            errors.append('Bank statements do not cover the entire requested financial year.')
        if date.fromisoformat(sorted_rows[0]['period_start'])<start or date.fromisoformat(sorted_rows[-1]['period_end'])>end:
            errors.append('Statement period extends beyond the financial year; boundary-day balances need additional transaction review.')
        for a,b in zip(sorted_rows,sorted_rows[1:]):
            pa=date.fromisoformat(a['period_end']);pb=date.fromisoformat(b['period_start'])
            if (pb-pa).days != 1:errors.append(f'Missing or overlapping statement dates: {a["source"]} → {b["source"]}')
            if Decimal(a['closing']) != Decimal(b['opening']):errors.append(f'Balance discontinuity: {a["source"]} closing does not equal {b["source"]} opening.')
    return dict(ready=not errors,errors=errors,rows=sorted_rows,
                opening=sorted_rows[0].get('opening'),closing=sorted_rows[-1].get('closing'))

def propose_bank_rows(doc):
    """Best-effort auto mapping; ambiguous signed amount exports are excluded from this shortcut."""
    candidates=[];exceptions=[]
    for table in doc.tables:
        found=False
        for header in range(1,min(9,len(table.rows))+1):
            names,records=fields(table,header)
            date_col=guess_field(names,'date');deposit=guess_field(names,'deposit');withdraw=guess_field(names,'withdrawal')
            amount=guess_field(names,'amount');direction=guess_field(names,'direction')
            if not date_col or not (deposit or withdraw or (amount and direction)):continue
            m={'date':date_col,'deposit':deposit,'withdrawal':withdraw,'amount':amount,
               'direction':direction,'description':guess_field(names,'description'),
               'reference':guess_field(names,'reference'),'account_code':guess_field(names,'account_code')}
            rows,issues,skipped=convert_records(records,'bank',m,doc.name,source_ref='DOC-'+doc.sha256[:10].upper())
            if rows or issues:
                candidates.extend(rows)
                exceptions.extend(f'{table.label}: {x}' for x in issues)
                if skipped:exceptions.append(f'{table.label}: {len(skipped)} rows excluded as headers/totals/invalid dates; review the source.')
                found=True;break
        if not found:exceptions.append(f'{table.label}: no reliable transaction columns identified; use manual column mapping.')
    dedup=existing_duplicates([],candidates,'bank')
    if dedup:exceptions.append(f'{len(dedup)} repeated transaction row(s) detected inside the upload.')
    candidates=[x for i,x in enumerate(candidates) if i not in set(dedup)]
    return candidates,exceptions
