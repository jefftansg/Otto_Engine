"""Conservative OCBC Daily Statement of Account - Details proposals.

Ledger Balance is a candidate only when printed totals reconcile. Selected
future end dates do not establish coverage beyond the print date.
"""
from datetime import date
from decimal import Decimal
import re
from .bank_headers import header_lines


def extract(doc):
    from .autofill import _money_candidates,_date,DATE_RX
    head=header_lines(doc);all_lines=[re.sub(r'\s+',' ',line).strip() for line in doc.text_excerpt.splitlines() if line.strip()]
    if not any(re.search(r'^Daily Statement of Account\s*[-–—]\s*Details$',line,re.I) for line in head):return None
    if not any(re.search(r'\bOVERSEA-CHINESE BANKING CORPORATION\b|\bOCBCSGSG(?:XXX)?\b',line,re.I) for line in head):return None
    errors=[]
    def one(values,label):
        unique=set(values)
        if len(unique)!=1:
            errors.append('Daily statement '+label+' is missing or conflicting.');return None
        return next(iter(unique))
    def amount(label):
        values=[]
        for line in head:
            m=re.search(r'\b'+label+r'\s*[:|]?\s*(.+)',line,re.I)
            if m:
                rest=re.split(r'\s+(?:Available Balance|Total Hold Amount|Ledger Balance|Opening Balance)\b',m.group(1),maxsplit=1,flags=re.I)[0]
                if re.search(r'\b(?:DR|OD|OVERDRAWN)\b',rest,re.I):
                    errors.append('Daily debit/overdraft notation requires manual review.');continue
                found=_money_candidates(rest)
                if len(found)==1:values.append(found[0])
        return one(values,label)
    opening,closing=amount('Opening Balance'),amount('Ledger Balance')
    totals={}
    for kind in ('Debits','Credits'):
        values=[]
        for line in head:
            m=re.match(kind+r'\s+(\d+)\s+Amount\s+(.+)',line,re.I)
            if m:
                rest=re.split(r'\s+(?:Available Balance|Total Hold Amount)\b',m.group(2),maxsplit=1,flags=re.I)[0]
                found=_money_candidates(rest)
                if len(found)==1:values.append((int(m.group(1)),found[0]))
        totals[kind]=one(values,kind+' count/amount')
    periods=[]
    for line in head:
        m=re.fullmatch(r'From\s+('+DATE_RX+r')\s+To\s+('+DATE_RX+r')',line,re.I)
        if m:
            low,high=_date(m.group(1)),_date(m.group(2))
            if low and high and low<=high:periods.append((low,high))
    period=one(periods,'explicit period');low,requested_end=period or (None,None)
    printed=[]
    for line in all_lines:
        m=re.match(r'Printed On\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',line,re.I)
        if m and _date(m.group(1)):printed.append(_date(m.group(1)))
    printed_on=one(printed,'print date')
    verified_end=min(printed_on,requested_end) if printed_on and requested_end else None
    if low and verified_end and verified_end<low:
        errors.append('Daily statement print date precedes its selected reporting period.');verified_end=None
    if printed_on and requested_end and printed_on<requested_end:
        errors.append('Statement printed on '+printed_on+' before selected period end '+requested_end+'; later dates are not covered.')
    if None not in (opening,closing,totals['Debits'],totals['Credits']):
        if opening+totals['Credits'][1]-totals['Debits'][1]!=closing:
            errors.append('Daily opening plus printed credits less debits differs from Ledger Balance.');closing=None
        for count,value in totals.values():
            if value<0 or (count==0)!=(value==0):errors.append('Daily transaction count/total is inconsistent.')
    return dict(profile='ocbc-daily-details-v1',bank='OCBC',opening=str(opening) if opening is not None else None,
                closing=str(closing) if closing is not None else None,period_start=low,period_end=verified_end,
                requested_period_end=requested_end,printed_on=printed_on,coverage_verified_through=verified_end,
                debit_count=totals['Debits'][0] if totals['Debits'] else None,debit_total=str(totals['Debits'][1]) if totals['Debits'] else None,
                credit_count=totals['Credits'][0] if totals['Credits'] else None,credit_total=str(totals['Credits'][1]) if totals['Credits'] else None,
                errors=errors)


def propose_rows(doc):
    from .autofill import _money_candidates,_date
    profile=extract(doc)
    if not profile:return [],['No supported OCBC daily-details layout.']
    # A partial extract may be reviewed, but cannot be imported as a complete period.
    if profile['errors']:return [],profile['errors']
    if not any(re.search(r'^Account Number\s+[\d -]+\s*-\s*SGD\b',line,re.I) for line in header_lines(doc)):
        return [],['Daily account currency must be explicitly SGD.']
    lines=[re.sub(r'\s+',' ',line).strip() for line in doc.text_excerpt.splitlines() if line.strip()]
    raw=[];active=False;errors=[]
    for idx,line in enumerate(lines):
        if re.match(r'^Post Date\b.*\bDebit Amount\b.*\bCredit Amount\b.*\bBalance\b',line,re.I):active=True;continue
        if re.match(r'^Printed (?:By|On)\b',line,re.I):active=False
        if not active:continue
        m=re.match(r'^(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\s+(.+)$',line)
        if not m:continue
        values=_money_candidates(m.group(2))
        if not values:continue  # Value-date/detail line; count and running totals still must tie.
        if len(values)!=2:
            errors.append('Daily source line '+str(idx+1)+': amount and running balance are ambiguous.');continue
        posted=_date(m.group(1));amount,balance=values
        if not posted or not profile['period_start']<=posted<=profile['period_end']:
            errors.append('Daily posting date is outside the selected/verified statement period; review the posting/value-date basis without silently backdating.');continue
        description=re.sub(r'\s+\(?-?[\d,]+\.\d{2}\)?\s+\(?-?[\d,]+\.\d{2}\)?\s*$','',m.group(2)).strip()
        details=[]
        for following in lines[idx+1:]:
            if re.match(r'^Printed\b|^Post Date\b',following,re.I):break
            next_date=re.match(r'^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\s+(.+)$',following)
            if next_date and _money_candidates(next_date.group(1)):break
            details.append(following)
        raw.append(dict(date=posted,source_reference=description,description=description+(' | '+' | '.join(details) if details else ''),amount=amount,balance=balance,line=idx+1))
    if errors:return [],errors
    expected=profile['debit_count']+profile['credit_count']
    if len(raw)!=expected:return [],['Daily extracted transaction count differs from the printed debit/credit counts.']
    valid=[]
    for ordered in (raw,list(reversed(raw))):
        previous=Decimal(profile['opening']);rows=[];ok=True;last_date=profile['period_start']
        for r in ordered:
            change=r['balance']-previous
            if r['date']<last_date or r['amount']<=0 or abs(change)!=r['amount']:ok=False;break
            rows.append(dict(date=r['date'],description=r['description'],reference='OCBC-'+doc.sha256[:10]+'-'+str(r['line']),
                deposit=str(r['amount']) if change>0 else '',withdrawal=str(r['amount']) if change<0 else '',account_code='9999',
                evidence_ref='DOC-'+doc.sha256[:10].upper(),source_reference=r['source_reference'],
                notes='Review-only OCBC daily details; printed counts/totals and running balances checked. Posting date retained; source line '+str(r['line'])+'.'))
            previous=r['balance'];last_date=r['date']
        if not ok:continue
        credits=sum((Decimal(r['deposit'] or '0') for r in rows),Decimal('0'));debits=sum((Decimal(r['withdrawal'] or '0') for r in rows),Decimal('0'))
        if (previous!=Decimal(profile['closing']) or credits!=Decimal(profile['credit_total']) or debits!=Decimal(profile['debit_total'])
            or sum(bool(r['deposit']) for r in rows)!=profile['credit_count'] or sum(bool(r['withdrawal']) for r in rows)!=profile['debit_count']):continue
        if rows not in valid:valid.append(rows)
    if len(valid)!=1:return [],['Daily transaction order, directions or running balances do not reconcile uniquely to printed totals.']
    return valid[0],[]
