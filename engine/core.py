"""Local-first, deterministic Singapore bookkeeping and reporting engine powering Otto.

Accounting reports are *drafts* requiring independent professional/director review.
No model inference, government filing or automatic compliance certification.
"""
from __future__ import annotations
import csv
import io
import json
import re
import zipfile
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

D = Decimal
CENT = D('0.01')

COA = [
    ('1000', 'Cash at bank', 'Asset', 'Cash and cash equivalents', 'Operating'),
    ('1100', 'Trade receivables', 'Asset', 'Trade receivables', 'Operating'),
    ('1200', 'Prepayments and deposits', 'Asset', 'Other current assets', 'Operating'),
    ('1500', 'Property and equipment', 'Asset', 'Non-current assets', 'Investing'),
    ('2000', 'Trade payables', 'Liability', 'Trade and other payables', 'Operating'),
    ('2100', 'Amount due to director - Director A', 'Liability', 'Amounts due to directors', 'Financing'),
    ('2101', 'Amount due to director - Director B', 'Liability', 'Amounts due to directors', 'Financing'),
    ('2200', 'Accruals and other liabilities', 'Liability', 'Other current liabilities', 'Operating'),
    ('2300', 'Borrowings', 'Liability', 'Borrowings', 'Financing'),
    ('3100', 'Share capital', 'Equity', 'Share capital', 'Financing'),
    ('3300', 'Retained earnings brought forward', 'Equity', 'Retained earnings', 'Financing'),
    ('4000', 'Sales and services revenue', 'Revenue', 'Revenue', 'Operating'),
    ('4100', 'Other income', 'Revenue', 'Other income', 'Operating'),
    ('5100', 'Bank charges', 'Expense', 'Bank charges', 'Operating'),
    ('5200', 'Office and rental expense', 'Expense', 'Office and rental', 'Operating'),
    ('5300', 'Advertising and marketing', 'Expense', 'Advertising and marketing', 'Operating'),
    ('5400', 'Software subscriptions', 'Expense', 'Software subscriptions', 'Operating'),
    ('5500', 'Professional fees', 'Expense', 'Professional fees', 'Operating'),
    ('5600', 'Other operating expenses', 'Expense', 'Other operating expenses', 'Operating'),
    ('5700', 'Depreciation', 'Expense', 'Depreciation', 'Noncash'),
    ('5800', 'Income tax expense', 'Expense', 'Income tax expense', 'Operating'),
    ('9999', 'Suspense / classification required', 'Asset', 'Suspense / review required', 'Unallocated'),
]
COA_MAP = {row[0]: {'code': row[0], 'name': row[1], 'type': row[2], 'group': row[3], 'cashflow': row[4]} for row in COA}
ALLOWED_FILES = ('company.json','bank.csv','claims.csv','journals.csv','invoices.csv','evidence.csv')


def money(value, label='amount') -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(CENT, rounding=ROUND_HALF_UP)
    raw = str(value if value is not None else '').strip().replace(',','')
    if raw in ('', '-', '—'): return D('0.00')
    if raw.startswith('(') and raw.endswith(')'): raw = '-' + raw[1:-1]
    try:
        n = D(raw).quantize(CENT, rounding=ROUND_HALF_UP)
        if not n.is_finite(): raise ValueError(label + ' must be finite')
        return n
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f'Invalid {label}: {value!r}') from e


def money_str(value): return f'{money(value):,.2f}'


def parse_date(value, label='date'):
    raw = str(value).strip()
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y'):
        try: return datetime.strptime(raw, fmt).date()
        except ValueError: pass
    raise ValueError(f'{label} must be YYYY-MM-DD or DD/MM/YYYY; got {value!r}')


def load_csv(text):
    if not text.strip(): return []
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    return [{k.strip() if k else '': (v or '').strip() for k,v in r.items()} for r in reader]


def csv_bytes(rows, columns):
    out=io.StringIO(newline=''); writer=csv.DictWriter(out, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({col: str(row.get(col,'')) for col in columns})
    return out.getvalue().encode('utf-8-sig')


class Package:
    def __init__(self, config, bank=None, claims=None, journals=None, invoices=None, evidence=None):
        self.config=dict(config)
        self.bank=list(bank or []); self.claims=list(claims or [])
        self.journals=list(journals or []); self.invoices=list(invoices or []); self.evidence=list(evidence or [])

    @classmethod
    def from_directory(cls, path):
        root=Path(path)
        def read(n): return (root/n).read_text(encoding='utf-8-sig') if (root/n).exists() else ''
        return cls(json.loads(read('company.json')), *(load_csv(read(n)) for n in ALLOWED_FILES[1:]))

    @classmethod
    def from_zip(cls, file_bytes):
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            contents={}
            for n in z.namelist():
                name=Path(n).name
                if name in ALLOWED_FILES:
                    if name in contents: raise ValueError('Duplicate package file: '+name)
                    if z.getinfo(n).file_size > 5_000_000: raise ValueError('File too large: '+name)
                    contents[name]=z.read(n).decode('utf-8-sig')
            if 'company.json' not in contents: raise ValueError('The ZIP must contain company.json')
            return cls(json.loads(contents['company.json']), *(load_csv(contents.get(n,'')) for n in ALLOWED_FILES[1:]))

    def to_zip(self):
        columns={
          'bank.csv':['date','description','reference','deposit','withdrawal','account_code','evidence_ref','notes'],
          'claims.csv':['claim_id','date','director','merchant','description','amount','expense_account','evidence_ref','notes'],
          'journals.csv':['journal_id','date','account_code','debit','credit','description','evidence_ref'],
          'invoices.csv':['invoice_no','date','due_date','customer','amount','amount_paid','evidence_ref'],
          'evidence.csv':['evidence_ref','document_type','source_file','remarks','review_status'],
        }
        bio=io.BytesIO()
        with zipfile.ZipFile(bio,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('company.json',json.dumps(self.config,indent=2,ensure_ascii=False))
            for n,cols in columns.items(): z.writestr(n,csv_bytes(getattr(self,n[:-4] if n!='journals.csv' else 'journals'),cols))
        return bio.getvalue()


def _entry(jid, dt, code, debit, credit, description, source, evidence=''):
    return {'journal_id':jid,'date':dt,'account_code':str(code),'debit':money(debit),'credit':money(credit),
            'description':str(description),'source':source,'evidence_ref':str(evidence)}


def generate(pkg:Package):
    errors=[]; warnings=[]; entries=[]; flow_items=[]
    cfg=pkg.config
    if not cfg.get('company_name') or not cfg.get('uen'): errors.append('Company name and UEN must be populated.')
    try:
        start=parse_date(cfg['fy_start']); end=parse_date(cfg['fy_end'])
        if end < start: errors.append('Financial year end precedes start.')
    except (ValueError,KeyError) as e: errors.append(str(e)); start=date.min; end=date.max
    if cfg.get('reporting_framework') not in ('SFRS for Small Entities','FRS'):
        errors.append('Choose SFRS for Small Entities or FRS; eligibility is a management decision.')
    if cfg.get('currency','SGD') != 'SGD': errors.append('V1 supports SGD only; no FX conversion.')
    by_dir={d['name'].strip():str(d['loan_account']) for d in cfg.get('directors',[]) if d.get('name')}
    for name,code in by_dir.items():
        if code not in COA_MAP or COA_MAP[code]['type']!='Liability': errors.append(f'Director {name}: invalid director loan account {code}.')
    bank_ref=set(); claim_ids=set(); inv_ids=set(); evidence_ids=set()
    for item in pkg.evidence:
        ref=item.get('evidence_ref','').strip()
        if ref in evidence_ids and ref: warnings.append('Duplicate evidence reference: '+ref)
        evidence_ids.add(ref)
        if item.get('review_status','').lower() not in ('reviewed','verified','approved'):
            warnings.append('Evidence not reviewed: '+(ref or '(unidentified)'))

    for i,r in enumerate(pkg.bank,1):
        try:
            dt=parse_date(r.get('date',''),f'Bank row {i} date')
            if not start <= dt <= end:
                errors.append(f'Bank row {i} is outside financial year.'); continue
            credit=money(r.get('deposit',''),f'bank row {i} deposit')
            debit=money(r.get('withdrawal',''),f'bank row {i} withdrawal')
            if credit<0 or debit<0 or (credit>0)==(debit>0):
                errors.append(f'Bank row {i}: enter exactly one positive deposit or withdrawal.'); continue
            ref=r.get('reference','').strip()
            if ref:
                if ref in bank_ref: errors.append(f'Duplicate bank reference: {ref}')
                bank_ref.add(ref)
            else: warnings.append(f'Bank row {i}: no bank reference; review for duplicates.')
            code=str(r.get('account_code','9999')).strip() or '9999'
            if code not in COA_MAP: errors.append(f'Bank row {i}: unknown account {code}.'); continue
            if code=='1000': errors.append(f'Bank row {i}: counter-account cannot also be the bank account.'); continue
            if code=='9999': errors.append(f'Bank row {i}: unresolved classification (suspense).')
            jid=f'BANK-{i:04d}'
            desc=r.get('description','')
            ev=r.get('evidence_ref','')
            entries.extend([_entry(jid,dt,'1000',credit,debit,desc,'Bank',ev),
                            _entry(jid,dt,code,debit,credit,desc,'Bank',ev)])
            cat=COA_MAP[code]['cashflow']
            if cat == 'Noncash':
                errors.append(
                    f'Bank row {i}: cash movement mapped to noncash account {code}. '
                    'Choose a cash-flow-appropriate counter-account.'
                )
                cat = 'Unallocated'
            flow_items.append({'date':dt,'journal_id':jid,'description':desc,'category':cat,'cash_movement':credit-debit})
        except ValueError as e: errors.append(str(e))

    bank_total = sum((item['cash_movement'] for item in flow_items), D('0'))

    for i,r in enumerate(pkg.claims,1):
        try:
            dt=parse_date(r.get('date',''),f'Claim {i} date')
            if not start <= dt <= end: errors.append(f'Claim {i} outside financial year.'); continue
            cid=r.get('claim_id','').strip()
            if not cid: errors.append(f'Claim row {i} missing claim ID.'); continue
            if cid in claim_ids: errors.append('Duplicate expense claim ID: '+cid)
            claim_ids.add(cid)
            amt=money(r.get('amount',''),f'claim {cid} amount')
            if amt<=0: errors.append('Expense claim amount must be positive: '+cid); continue
            code=str(r.get('expense_account','')).strip()
            director=r.get('director','').strip()
            loan=by_dir.get(director)
            if not loan: errors.append(f'Claim {cid}: unknown director {director!r}.'); continue
            if code not in COA_MAP: errors.append(f'Claim {cid}: unknown account {code}.'); continue
            if COA_MAP[code]['type'] not in ('Expense','Asset'):
                errors.append(f'Claim {cid}: expected an expense or asset account, got {code}.'); continue
            desc=r.get('description','') or r.get('merchant','')
            ev=r.get('evidence_ref','')
            entries.extend([_entry(cid,dt,code,amt,0,desc,'Director claim',ev),
                            _entry(cid,dt,loan,0,amt,desc,'Director claim',ev)])
        except ValueError as e: errors.append(str(e))

    for i,r in enumerate(pkg.journals,1):
        try:
            jid=r.get('journal_id','').strip()
            if not jid: errors.append(f'Manual journal row {i} missing journal ID.'); continue
            dt=parse_date(r.get('date',''),f'Manual row {i} date')
            if dt>end: errors.append(f'Manual journal row {i} after financial year end.'); continue
            code=str(r.get('account_code','')).strip()
            if code not in COA_MAP: errors.append(f'Manual row {i}: invalid account {code}'); continue
            debit=money(r.get('debit',''),f'manual row {i} debit')
            credit=money(r.get('credit',''),f'manual row {i} credit')
            if debit<0 or credit<0 or (debit>0)==(credit>0): errors.append(f'Manual row {i}: enter one positive debit or credit.'); continue
            entries.append(_entry(jid,dt,code,debit,credit,r.get('description',''),'Manual',r.get('evidence_ref','')))
        except ValueError as e: errors.append(str(e))

    journal_sources = {}
    by_journal=defaultdict(lambda:[D('0'),D('0'),0])
    for e in entries:
        jid = e['journal_id']
        source_type = e['source']
        first_source = journal_sources.setdefault(jid, source_type)
        if first_source != source_type:
            errors.append(f'Journal ID collision: {jid} is used by {first_source} and {source_type}.')
        v=by_journal[(source_type, jid)]; v[0]+=e['debit']; v[1]+=e['credit']; v[2]+=1
    for (_, jid),(dr,cr,n) in by_journal.items():
        if dr!=cr: errors.append(f'Journal {jid} unbalanced: debit {money_str(dr)} vs credit {money_str(cr)}.')
        if n<2: warnings.append(f'Journal {jid} has fewer than two lines.')
    manual_entries = (entry for entry in entries if entry['source'] == 'Manual')
    for jid,lines in _group(manual_entries,'journal_id').items():
        if lines[0]['source']=='Manual':
            cash=[l for l in lines if l['account_code']=='1000' and start<=l['date']<=end]
            if cash:
                cats={COA_MAP[l['account_code']]['cashflow'] for l in lines if l['account_code']!='1000'}
                cat=next(iter(cats)) if len(cats)==1 else 'Unallocated'
                if cat=='Unallocated': errors.append(f'Manual cash journal {jid} has mixed classifications; split into separate journals.')
                elif cat == 'Noncash':
                    errors.append(
                        f'Manual cash journal {jid}: cash movement mapped to a noncash account. '
                        'Review the counter-account before reporting.'
                    )
                    cat = 'Unallocated'
                flow_items.append({'date':cash[0]['date'],'journal_id':jid,'description':cash[0]['description'],
                                   'category':cat,'cash_movement':sum((l['debit']-l['credit'] for l in cash),D('0'))})
    balances=defaultdict(lambda:D('0')); prev=defaultdict(lambda:D('0'))
    for e in entries:
        balances[e['account_code']]+=e['debit']-e['credit']
        if e['date']<start: prev[e['account_code']]+=e['debit']-e['credit']
    period=defaultdict(lambda:D('0'))
    for e in entries:
        if start<=e['date']<=end: period[e['account_code']]+=e['debit']-e['credit']
    revenue=sum((-v for c,v in period.items() if COA_MAP[c]['type']=='Revenue'),D('0'))
    expenses=sum((v for c,v in period.items() if COA_MAP[c]['type']=='Expense'),D('0'))
    profit=revenue-expenses
    opening_profit=sum((-v for c,v in prev.items() if COA_MAP[c]['type']=='Revenue'),D('0'))-sum((v for c,v in prev.items() if COA_MAP[c]['type']=='Expense'),D('0'))
    assets=sum((v for c,v in balances.items() if COA_MAP[c]['type']=='Asset'),D('0'))
    liabilities=sum((-v for c,v in balances.items() if COA_MAP[c]['type']=='Liability'),D('0'))
    booked_equity=sum((-v for c,v in balances.items() if COA_MAP[c]['type']=='Equity'),D('0'))
    equity=booked_equity+opening_profit+profit
    if assets!=liabilities+equity:
        errors.append('Balance sheet out of balance: assets not equal liabilities plus equity.')
    debits=sum((v for v in balances.values() if v>0),D('0'))
    credits=sum((-v for v in balances.values() if v<0),D('0'))
    if debits!=credits: errors.append('Trial balance totals are unequal.')
    opening_value = cfg.get('bank_statement_opening')
    opening_missing = opening_value is None or not str(opening_value).strip()
    if opening_missing:
        errors.append('Bank statement opening balance is required.')
    closing_value = cfg.get('bank_statement_closing')
    closing_missing = closing_value is None or not str(closing_value).strip()
    if closing_missing:
        errors.append('Bank statement closing balance is required.')
    try:
        bank_open = D('0') if opening_missing else money(opening_value, 'bank opening balance')
        bank_end = D('0') if closing_missing else money(closing_value, 'bank closing balance')
    except ValueError as e:
        errors.append(str(e));bank_open=bank_end=D('0')
    ledger_open=prev['1000']
    ledger_end=balances['1000']
    if not opening_missing and bank_open != ledger_open: errors.append(f'Opening bank statement {money_str(bank_open)} differs from opening ledger {money_str(ledger_open)}.')
    if not (opening_missing or closing_missing) and bank_end != bank_open + bank_total:
        errors.append(f'Bank statement closing does not reconcile with imported bank transactions: {money_str(bank_open+bank_total)} expected, {money_str(bank_end)} entered.')
    if not closing_missing and bank_end != ledger_end: errors.append(f'Closing bank statement {money_str(bank_end)} differs from bank ledger {money_str(ledger_end)}.')
    cashflows=defaultdict(lambda:D('0'))
    for f in flow_items: cashflows[f['category']]+=f['cash_movement']
    for category in ('Operating','Investing','Financing','Unallocated'):
        cashflows[category]+=D('0')
    cash_change=sum(cashflows.values(),D('0'))
    if cash_change!=ledger_end-ledger_open: errors.append('Cash flow total does not agree with change in bank balance.')
    if cashflows['Unallocated']!=0: errors.append('Cash flow contains unallocated amounts.')

    receivables=[]; inv_total=D('0')
    for i,r in enumerate(pkg.invoices,1):
        try:
            ino=r.get('invoice_no','').strip()
            if not ino or ino in inv_ids: errors.append(f'Invoice {i}: blank/duplicate invoice number.'); continue
            inv_ids.add(ino)
            dt=parse_date(r.get('date',''),f'invoice {ino} date'); due=parse_date(r.get('due_date',''),f'invoice {ino} due date')
            if dt>end: continue
            amt=money(r.get('amount',''),f'invoice {ino} total'); paid=money(r.get('amount_paid',''),f'invoice {ino} amount paid')
            if amt<0 or paid<0 or paid>amt: errors.append(f'Invoice {ino}: invalid total or paid amount.'); continue
            unpaid=amt-paid
            if unpaid:
                days=(end-due).days
                ageing='Current' if days<=0 else '1-30' if days<=30 else '31-60' if days<=60 else '61-90' if days<=90 else '91+'
                receivables.append({'invoice_no':ino,'customer':r.get('customer',''),'due_date':due,
                    'outstanding':unpaid,'bucket':ageing,'evidence_ref':r.get('evidence_ref','')})
                inv_total+=unpaid
        except ValueError as e: errors.append(str(e))
    if inv_total!=balances['1100']:
        errors.append(f'AR invoice schedule {money_str(inv_total)} does not agree with receivables ledger {money_str(balances["1100"])}.')
    for e in entries:
        if e['evidence_ref'] and e['evidence_ref'] not in evidence_ids:
            warnings.append(f"Evidence ref {e['evidence_ref']} (journal {e['journal_id']}) is absent from evidence.csv.")
        if not e['evidence_ref'] and e['source']!='Manual': warnings.append(f"Missing evidence reference for {e['journal_id']}.")
    if not cfg.get('bank_balances_confirmed'):
        warnings.append('Opening/closing bank statement balances have not been confirmed. Statement arithmetic alone is insufficient to establish the opening ledger position.')
    if not cfg.get('fy_confirmed',False):
        warnings.append('Financial year start and year-end have not been explicitly confirmed in the setup wizard.')
    if not cfg.get('framework_eligibility_confirmed'):
        warnings.append('Management has not confirmed eligibility for the selected reporting framework.')
    if not cfg.get('director_review_confirmed'):
        warnings.append('Director review/approval has not been confirmed; outputs remain draft.')
    if not cfg.get('disclosures_reviewed'):
        warnings.append('Required disclosures, going concern, related-party and comparatives must be reviewed.')
    if cfg.get('entity_type')!='Private limited company':
        warnings.append('Company-form UFS is for private limited companies only; other entities should use management accounts.')
    errors=list(dict.fromkeys(errors));warnings=list(dict.fromkeys(warnings))
    return {'config':cfg,'start':start,'end':end,'entries':sorted(entries,key=lambda e:(e['date'],e['journal_id'])),
            'balances':dict(balances),'period':dict(period),'opening':dict(prev),'flows':flow_items,
            'cashflows':dict(cashflows),'receivables':receivables,'revenue':revenue,'expenses':expenses,
            'profit':profit,'assets':assets,'liabilities':liabilities,'equity':equity,
            'booked_equity':booked_equity,'opening_profit':opening_profit,'bank_open':bank_open,
            'bank_close':bank_end,'bank_delta':bank_total,'ledger_open':ledger_open,'ledger_end':ledger_end,
            'bank_open_missing': opening_missing,
            'bank_close_missing': closing_missing,
            'trial_debit':debits,'trial_credit':credits,'errors':errors,'warnings':warnings,'package':pkg}


def _group(items,key):
    out=defaultdict(list)
    for item in items: out[item[key]].append(item)
    return out


def balance_sheet_rows(result):
    rows=[]
    for group in ('Asset','Liability','Equity'):
        for code,v in sorted(result['balances'].items()):
            if COA_MAP[code]['type']!=group or not v:continue
            rows.append([code,COA_MAP[code]['name'],money_str(v if group=='Asset' else -v)])
        if group=='Equity':
            if result['opening_profit']:rows.append(['','Prior-period unclosed profit / loss',money_str(result['opening_profit'])])
            rows.append(['','Current-year profit / loss',money_str(result['profit'])])
    return rows


def profit_rows(result):
    rows=[]
    for group in ('Revenue','Expense'):
        for code,v in sorted(result['period'].items()):
            if COA_MAP[code]['type']==group and v:
                rows.append([code,COA_MAP[code]['name'],money_str(-v if group=='Revenue' else v)])
    return rows


def trial_rows(result):
    rows=[]
    for code,amount in sorted(result['balances'].items()):
        if amount:
            rows.append([code,COA_MAP[code]['name'],money_str(max(amount,D(0))),money_str(max(-amount,D(0)))])
    rows.append(['','TOTAL',money_str(result['trial_debit']),money_str(result['trial_credit'])])
    return rows


def director_balances(result):
    return [(d['name'],d['loan_account'],-result['balances'].get(str(d['loan_account']),D('0'))) for d in result['config'].get('directors',[])]
