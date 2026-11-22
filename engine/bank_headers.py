"""Bank header identity only: transaction counterparties are never account holders."""
import re

# Stop before transaction columns, dated transaction rows, and print/footer metadata.
STOP = re.compile(r'^(?:Post\s+Date\b|Transaction\s+(?:Value|Date)\b|Date\s+(?:Description|Details|Bank\s+Ref)\b|Value\s+Date\b|Printed\s+(?:By|On)\b|(?:\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b)',re.I)
RIGHT_FIELD = re.compile(r'(?:^|\s+)(?:Ledger\s+Balance|Opening\s+Balance|Closing\s+Balance|Available\s+Balance|Total\s+Hold\s+Amount)\b',re.I)
OWNER = re.compile(r'^(?:Company\s+Name|Account\s+Name|Account\s+Holder)\s*[:|]?\s*(.*)$',re.I)
HEADING = re.compile(r"([A-Z0-9][A-Z0-9 &.,()/'-]*?\b(?:PTE\.?\s+LTD\.?|PRIVATE LIMITED|LLP))\s*(?:STATEMENT OF ACCOUNT)?")


def header_lines(doc):
    raw=doc.text_excerpt.splitlines()
    if not raw:raw=[' '.join(row) for table in doc.tables for row in table.rows[:40]]
    result=[]
    for raw_line in raw[:80]:
        line=re.sub(r'\s+',' ',raw_line).strip()
        if not line:continue
        if STOP.search(line):
            from .importers import parse_iso_date
            parts=re.split(r'\s+(?:TO|THROUGH|UNTIL)\s+',line,flags=re.I)
            try:
                is_period=len(parts)==2 and all(parse_iso_date(part) for part in parts)
            except ValueError:is_period=False
            if not is_period:break
        result.append(line)
    return result


def account_holder(doc):
    lines=header_lines(doc);labelled=[];label_seen=False
    for i,line in enumerate(lines):
        match=OWNER.match(line)
        if not match:continue
        label_seen=True;value=RIGHT_FIELD.split(match.group(1),maxsplit=1)[0].strip(' :|')
        if not value and i+1<len(lines) and not re.match(r'^(?:Account|Opening|Closing|Ledger|Currency|Debits|Credits|BIC)\b',lines[i+1],re.I):
            value=RIGHT_FIELD.split(lines[i+1],maxsplit=1)[0].strip(' :|')
        if value and len(value)<=180:labelled.append((value,line))
    if not label_seen and any(re.search(r'STATEMENT\s+OF\s+ACCOUNT|BANK\s+STATEMENT',line,re.I) for line in lines):
        labelled=[(m.group(1),line) for line in lines for m in [HEADING.fullmatch(line)] if m]
    unique={re.sub('[^A-Z0-9]','',value.upper()) for value,_ in labelled}
    if len(unique)>1:return dict(value='',line='',errors=['Conflicting account-holder fields in the statement header.'])
    if labelled:return dict(value=labelled[0][0],line=labelled[0][1],errors=[])
    return dict(value='',line='',errors=[])
