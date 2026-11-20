"""Local, review-first ingestion of CSV, Excel and text-based PDF tables.

No imported values are posted until the user confirms a field mapping and preview.
Scanned PDFs, ambiguous amounts and unparseable rows remain exceptions.
"""
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO, StringIO, TextIOWrapper
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import re
from .core import money

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_ROWS = 20_000
MAX_PDF_PAGES = 80
MAX_COLUMNS = 65


@dataclass
class SourceTable:
    label: str
    rows: list[list[str]]


@dataclass
class SourceDocument:
    name: str
    sha256: str
    tables: list[SourceTable]
    text_excerpt: str = ''
    pages: int = 0
    notes: tuple[str, ...] = ()


def _s(v):
    if v is None: return ''
    if isinstance(v, (datetime, date)): return v.strftime('%Y-%m-%d')
    if isinstance(v, (float,int)) and float(v).is_integer(): return str(int(v))
    return str(v).strip()


def _clean_rows(rows):
    result=[]
    for row in rows:
        if row is None: continue
        vals=[_s(v).replace('\n',' ').strip() for v in list(row)[:MAX_COLUMNS]]
        if any(vals): result.append(vals)
        if len(result)>MAX_ROWS: raise ValueError('File has more than 20,000 rows. Split into smaller files.')
    return result


def _decode_csv(data):
    for enc in ('utf-8-sig','utf-16','cp1252'):
        try:
            t=data.decode(enc)
            if '\ufffd' not in t: return t
        except (UnicodeError, UnicodeDecodeError): continue
    raise ValueError('Unsupported CSV encoding. Export as UTF-8 CSV.')


def inspect_document(filename, file_bytes):
    """Return available sheet/table previews; no accounting entries created."""
    if not file_bytes: raise ValueError('File is empty.')
    if len(file_bytes)>MAX_FILE_BYTES: raise ValueError('Maximum document size is 25 MB.')
    ext=filename.rsplit('.',1)[-1].lower()
    tables=[]; text=''; pages=0; notes=[]
    if ext=='csv':
        content=_decode_csv(file_bytes)
        try: dialect=csv.Sniffer().sniff(content[:8192], delimiters=',;\t|')
        except csv.Error: dialect=csv.excel
        tables=[SourceTable('CSV rows',_clean_rows(csv.reader(StringIO(content),dialect)))]
    elif ext=='xlsx':
        from openpyxl import load_workbook
        wb=load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
        try:
            for sheet in wb:
                if sheet.max_row and sheet.max_row>MAX_ROWS+200:
                    raise ValueError(f'Worksheet {sheet.title} exceeds row limit.')
                tables.append(SourceTable(sheet.title,_clean_rows(sheet.iter_rows(values_only=True))))
        finally: wb.close()
    elif ext=='xls':
        import xlrd
        wb=xlrd.open_workbook(file_contents=file_bytes, on_demand=True)
        try:
            for sheet in wb.sheets():
                if sheet.nrows>MAX_ROWS+200: raise ValueError(f'Worksheet {sheet.name} exceeds row limit.')
                raw=[]
                for ridx in range(sheet.nrows):
                    cells=[]
                    for c in range(min(sheet.ncols,MAX_COLUMNS)):
                        cell=sheet.cell(ridx,c)
                        if cell.ctype==xlrd.XL_CELL_DATE:
                            dt=xlrd.xldate_as_datetime(cell.value,wb.datemode)
                            cells.append(dt.strftime('%Y-%m-%d'))
                        else: cells.append(cell.value)
                    raw.append(cells)
                tables.append(SourceTable(sheet.name,_clean_rows(raw)))
        finally: wb.release_resources()
    elif ext=='pdf':
        import pdfplumber
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            pages=len(pdf.pages)
            if pages>MAX_PDF_PAGES:
                notes.append(f'PDF has {pages} pages; only first {MAX_PDF_PAGES} inspected.')
            for pno,page in enumerate(pdf.pages[:MAX_PDF_PAGES],start=1):
                page_text=page.extract_text() or ''
                if len(text)<250000: text+=(page_text+'\n')[:250000-len(text)]
                for i,table in enumerate(page.extract_tables() or [],start=1):
                    cleaned=_clean_rows(table)
                    if len(cleaned)>=2:
                        tables.append(SourceTable(f'Page {pno} / table {i}',cleaned))
        if not text.strip() and not tables:
            notes.append('Image-only/scanned PDF: no selectable text. OCR is not included; register as evidence or upload exported CSV/Excel.')
        elif not tables:
            notes.append('Text PDF has no reliable detected transaction table. Register as evidence, or obtain a CSV/Excel bank export.')
        else:
            notes.append('PDF-extracted tables may merge/split cells. Review every row before importing.')
    else: raise ValueError(f'Unsupported file type: .{ext}')
    return SourceDocument(filename,hashlib.sha256(file_bytes).hexdigest(),tables,text,pages,tuple(notes))


def fields(table, header_row=1):
    """Convert a raw table to headers and records. header_row is 1-indexed."""
    if not table.rows: return [],[]
    idx=max(0,min(int(header_row)-1,len(table.rows)-1))
    headers=[]; used={}
    for j,h in enumerate(table.rows[idx]):
        s=re.sub(r'\s+',' ',h).strip() or f'Column {j+1}'
        num=used.get(s,0)+1;used[s]=num
        headers.append(s if num==1 else f'{s} ({num})')
    out=[]
    for row in table.rows[idx+1:]:
        vals=(row+['']*len(headers))[:len(headers)]
        if any(x.strip() for x in vals): out.append(dict(zip(headers,vals)))
    return headers,out


SYNONYMS={
    'date':['transaction date','value date','posting date','date of transaction','date','trans date','trx date'],
    'description':['description','transaction details','transaction description','details','narration','particulars','remarks','reference description','payee','transaction'],
    'reference':['transaction reference','reference number','reference no','reference','ref no','ref','transaction id','document no','cheque no'],
    'deposit':['deposit','deposits','credit amount','credit(s)','credits','credit','money in','paid in','receipt','inflow'],
    'withdrawal':['withdrawal','withdrawals','debit amount','debit(s)','debits','debit','money out','payment','outflow'],
    'amount':['transaction amount','amount (sgd)','amount sgd','amount','sgd amount','net amount'],
    'direction':['transaction type','dr/cr','debit/credit','type','direction'],
    'account_code':['account code','account_code','gl code','ledger code','gl account'],
    'evidence_ref':['evidence ref','evidence_ref','source id','document ref'],
    'claim_id':['claim id','claim_id','expense id','expense number'],
    'director':['director','paid by','employee','claimant'],
    'merchant':['merchant','vendor','supplier','payee'],
    'expense_account':['expense account','expense_account','gl code','account code'],
    'invoice_no':['invoice number','invoice no','invoice_no','invoice #','inv no'],
    'due_date':['due date','payment due','due_date'],
    'customer':['customer','client','client name'],
    'amount_paid':['paid','paid amount','amount paid','amount_paid','settled'],
    'journal_id':['journal id','journal_id','journal no','entry id'],
}


def guess_field(headers,name):
    names=SYNONYMS.get(name,[name.replace('_',' ')])
    canon=lambda s:re.sub(r'[^a-z0-9]','',s.casefold())
    for candidate in names:
        for h in headers:
            if canon(h)==canon(candidate): return h
    return ''


def parse_iso_date(value):
    raw=_s(value).strip()
    formats=('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y','%d/%m/%y','%d-%m-%y',
             '%Y/%m/%d','%d %b %Y','%d %B %Y','%d %b %y','%d %B %y','%Y-%m-%d %H:%M:%S')
    for fmt in formats:
        try:return datetime.strptime(raw,fmt).date().isoformat()
        except ValueError:pass
    raise ValueError(f'Unrecognised date {raw!r}')


def parse_money(value):
    raw=_s(value).replace('S$','').replace('SGD','').replace('$','').replace(',','').strip()
    raw=raw.replace('−','-').replace('–','-')
    raw=re.sub(r'\s*(CR|DR)$','',raw, flags=re.I).strip()
    if not raw or raw in ('-','—'):return Decimal('0')
    if raw.startswith('(') and raw.endswith(')'):raw='-'+raw[1:-1]
    try:
        num=Decimal(raw)
        if not num.is_finite(): raise ValueError()
        return num.quantize(Decimal('0.01'))
    except (InvalidOperation,ValueError):raise ValueError(f'Unrecognised amount {value!r}')


def convert_records(records,kind,mapping,source_name,signed_mode='positive_deposit',source_ref=''):
    """Returns (proposed_rows, row_errors, skipped). No hidden financial guesses.

    `mapping` keys are standard target fields, values are uploaded column headings.
    """
    if kind not in ('bank','claims','invoices','journals'):raise ValueError('Unknown import type')
    out=[];issues=[];skipped=[]
    def get(rec,key):return rec.get(mapping.get(key,''),'') if mapping.get(key) else ''
    for i,rec in enumerate(records,1):
        dt=get(rec,'date')
        if not str(dt).strip():
            skipped.append(i); continue
        # Bank exports repeat column headers / summary lines; show these as skipped.
        try: date_iso=parse_iso_date(dt)
        except ValueError:
            skipped.append(i); continue
        try:
            evidence=source_ref or f'DOC-{hashlib.sha256(source_name.encode()).hexdigest()[:10].upper()}'
            if kind=='bank':
                deposit=parse_money(get(rec,'deposit')); withdrawal=parse_money(get(rec,'withdrawal'))
                if mapping.get('amount') and not mapping.get('deposit') and not mapping.get('withdrawal'):
                    raw_amount=get(rec,'amount'); amount=parse_money(raw_amount)
                    direction=_s(get(rec,'direction')).upper().strip()
                    if direction:
                        if direction in ('C','CR','CREDIT','DEPOSIT','IN','RECEIPT'):deposit=abs(amount)
                        elif direction in ('D','DR','DEBIT','WITHDRAWAL','OUT','PAYMENT'):withdrawal=abs(amount)
                        else:raise ValueError(f'unknown DR/CR direction {direction!r}')
                    else:
                        if signed_mode=='positive_deposit':
                            deposit=max(amount,Decimal('0'));withdrawal=max(-amount,Decimal('0'))
                        else:
                            withdrawal=max(amount,Decimal('0'));deposit=max(-amount,Decimal('0'))
                if deposit<0 or withdrawal<0 or (deposit>0)==(withdrawal>0):
                    raise ValueError('requires exactly one positive deposit or withdrawal')
                ref=_s(get(rec,'reference'))
                out.append(dict(date=date_iso,description=_s(get(rec,'description')),
                    reference=ref,deposit=str(deposit) if deposit else '',withdrawal=str(withdrawal) if withdrawal else '',
                    account_code=_s(get(rec,'account_code')) or '9999',evidence_ref=_s(get(rec,'evidence_ref')) or evidence,
                    notes=f'Imported from {source_name}; classification requires review'))
            elif kind=='claims':
                amt=parse_money(get(rec,'amount'))
                if amt<=0:raise ValueError('claim amount must be positive')
                out.append(dict(claim_id=_s(get(rec,'claim_id')) or f'CLAIM-{hashlib.sha256((source_name+str(i)).encode()).hexdigest()[:12]}',
                    date=date_iso,director=_s(get(rec,'director')),merchant=_s(get(rec,'merchant')),
                    description=_s(get(rec,'description')),amount=str(amt),
                    expense_account=_s(get(rec,'expense_account')) or '9999',
                    evidence_ref=_s(get(rec,'evidence_ref')) or evidence,notes=f'Imported from {source_name}; verify funding & account'))
            elif kind=='invoices':
                amount=parse_money(get(rec,'amount'));paid=parse_money(get(rec,'amount_paid'))
                if amount<0 or paid<0 or paid>amount:raise ValueError('invalid invoice amount or payment')
                due=parse_iso_date(get(rec,'due_date'))
                ino=_s(get(rec,'invoice_no'))
                if not ino:raise ValueError('missing invoice number')
                out.append(dict(invoice_no=ino,date=date_iso,due_date=due,customer=_s(get(rec,'customer')),
                    amount=str(amount),amount_paid=str(paid),evidence_ref=_s(get(rec,'evidence_ref')) or evidence))
            elif kind=='journals':
                debit=parse_money(get(rec,'debit'));credit=parse_money(get(rec,'credit'))
                if debit<0 or credit<0 or (debit>0)==(credit>0):raise ValueError('requires exactly one positive debit or credit')
                jid=_s(get(rec,'journal_id'))
                if not jid:raise ValueError('missing journal ID')
                out.append(dict(journal_id=jid,date=date_iso,account_code=_s(get(rec,'account_code')),
                    debit=str(debit) if debit else '',credit=str(credit) if credit else '',
                    description=_s(get(rec,'description')),evidence_ref=_s(get(rec,'evidence_ref')) or evidence))
        except ValueError as e:issues.append(f'Row {i}: {e}')
    return out,issues,skipped


def existing_duplicates(existing,candidates,kind):
    """Candidate row numbers already present based on a conservative signature."""
    import json
    if kind=='bank':
        keys=('date','description','reference','deposit','withdrawal')
    elif kind=='claims':keys=('claim_id',)
    elif kind=='invoices':keys=('invoice_no',)
    else: keys=('journal_id','date','account_code','debit','credit')
    def signature(r):return tuple(str(r.get(k,'')).strip().lower() for k in keys)
    old={signature(r) for r in existing};seen=set();duplicates=[]
    for i,row in enumerate(candidates):
        sig=signature(row)
        if sig in old or sig in seen:duplicates.append(i)
        seen.add(sig)
    return duplicates


def empty_company():
    # Deliberately unconfirmed; the setup wizard asks for actual FY end and opening.
    return dict(company_name='',uen='',entity_type='Private limited company',registered_address='',
        principal_activity='',fy_start='2026-01-01',fy_end='2026-12-31',fy_confirmed=False,
        reporting_framework='SFRS for Small Entities',currency='SGD',
        framework_eligibility_confirmed=False,director_review_confirmed=False,disclosures_reviewed=False,
        bank_statement_opening='0.00',bank_statement_closing='0.00',bank_balances_confirmed=False,
        statement_register=[],acra_source={},directors=[],
        revenue_policy='',accounting_policies='',going_concern_note='',other_disclosures='',document_checklist={})
