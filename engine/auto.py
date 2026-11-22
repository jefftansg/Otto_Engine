"""Local document-first analysis. Proposals never mutate the accounting package."""
from calendar import monthrange
from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
import json
import re

from .autofill import extract_acra_profile, extract_bank_statement, consolidate_statement_balances, propose_bank_rows
from .importers import inspect_document, existing_duplicates, MAX_FILE_BYTES
from .intake_review import upload_id

MAX_BATCH_FILES = 50
MAX_BATCH_BYTES = 100 * 1024 * 1024


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, default=str, separators=(',', ':')).encode()).hexdigest()


def canonical_name(name):
    return re.sub(r'[^A-Z0-9]', '', (name or '').upper())


def demonstration(doc):
    text = doc.name + '\n' + doc.text_excerpt
    return bool(re.search(r'\b(?:fictional|synthetic|demonstration|demo|not[ _-]+official|not[ _-]+a[ _-]+real)\b',
                          text.replace('_', ' '), re.I))


def company_name(doc):
    # Only explicitly labelled company fields or a company-name heading.
    lines = doc.text_excerpt.splitlines()[:80]
    for line in lines:
        match = re.match(r'^\s*(?:Company Name|Account Name|Account Holder)\s*:\s*(.+?)\s*$', line, re.I)
        if match:
            return match.group(1)
    for line in lines:
        match = re.fullmatch(r'\s*([A-Z0-9][A-Z0-9 &.,()/\'-]*?\b(?:PTE\.?\s+LTD\.?|PRIVATE LIMITED|LLP))\s*(?:STATEMENT OF ACCOUNT)?\s*', line)
        if match:
            return match.group(1)
    return ''


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def provenance(doc, value, field):
    source_lines=doc.text_excerpt.splitlines()+[' | '.join(row) for table in doc.tables for row in table.rows]
    lines = [line.strip() for line in source_lines if str(value).upper() in line.upper()]
    if field in ('opening', 'closing'):
        needle = 'B/F' if field == 'opening' else 'C/F'
        label=r'OPENING|BROUGHT|BEGINNING' if field=='opening' else r'CLOSING|CARRIED|ENDING'
        lines = [line.strip() for line in source_lines if needle in line.upper() or re.search(label,line,re.I)]
    if field in ('period_start','period_end') and not lines:
        lines=[line.strip() for line in source_lines if re.search(r'\d{1,2}\s+[A-Z]{3,9}\s+\d{4}\s+TO\s+\d{1,2}\s+[A-Z]{3,9}\s+\d{4}',line,re.I)]
    return dict(source=doc.name, sha256=doc.sha256, field=field, value=value,
                excerpt=lines[0][:300] if lines else '', confidence='Explicit source field; review required')


def coverage(statements, start, end):
    low, high = _date(start), _date(end)
    if not low or not high or low > high or (high-low).days>732:
        return dict(months=[], covered=0, expected=0, opening=None, opening_sources=[], latest_closing=None,
                    balances=dict(ready=False, errors=['Confirm reporting dates to check coverage.']))
    inside = [b for b in statements if _date(b.get('period_start')) and _date(b.get('period_end')) and
              _date(b['period_start']) <= high and _date(b['period_end']) >= low]
    months = []
    cursor = low.replace(day=1)
    while cursor <= high:
        a, b = max(low, cursor), min(high, cursor.replace(day=monthrange(cursor.year,cursor.month)[1]))
        spans = sorted((max(a,_date(s['period_start'])), min(b,_date(s['period_end']))) for s in inside
                       if _date(s['period_start']) <= b and _date(s['period_end']) >= a)
        upto = a.toordinal()
        for left,right in spans:
            if left.toordinal() > upto:
                break
            upto = max(upto,right.toordinal()+1)
        months.append(dict(month=cursor.strftime('%Y-%m'), status='Covered' if upto>b.toordinal() else 'Missing / incomplete'))
        if cursor.year==9999 and cursor.month==12:break
        cursor = (cursor.replace(day=28)+timedelta(days=4)).replace(day=1)
    candidates = []
    for s in statements:
        if _date(s.get('period_start')) == low and s.get('opening') is not None:
            candidates.append(dict(value=s['opening'], source=s['source'], sha256=s['sha256'], field='opening'))
        if _date(s.get('period_end')) == (low-timedelta(days=1) if low>date.min else None) and s.get('closing') is not None:
            candidates.append(dict(value=s['closing'], source=s['source'], sha256=s['sha256'], field='closing'))
    values = {Decimal(c['value']) for c in candidates}
    latest = max((s for s in inside if s.get('closing') is not None), key=lambda s:s['period_end'], default=None)
    balances = consolidate_statement_balances(inside,start,end)
    if len(values)>1:
        balances['ready']=False
        balances['errors'].append('Opening evidence conflicts with the previous-period closing balance.')
    return dict(months=months, covered=sum(m['status']=='Covered' for m in months), expected=len(months),
                opening=str(next(iter(values))) if len(values)==1 else None, opening_sources=candidates,
                latest_closing=dict(value=latest['closing'], date=latest['period_end'], source=latest['source']) if latest else None,
                balances=balances)


def analyse(files, config, inspect=inspect_document):
    if len(files)>MAX_BATCH_FILES or sum(len(f['bytes']) for f in files)>MAX_BATCH_BYTES:
        raise ValueError('Use at most 50 files and 100 MB per batch.')
    inventory=[]; parsed=[]; seen={}; groups=defaultdict(list); proposals=defaultdict(list)
    expected=canonical_name(config.get('company_name'))
    synthetic_test_mode=config.get('synthetic_test_mode') is True
    for item in files:
        row=dict(id=upload_id(item), name=item['name'], sha256=item['sha256'], type='Needs review',
                 status='Needs review', reasons=[], fields=[], company='')
        if sha256(item['bytes']).hexdigest()!=item['sha256']:
            raise ValueError('File fingerprint mismatch; upload the original again.')
        if item['sha256'] in seen:
            row.update(type='Duplicate', status='Excluded duplicate')
            row['reasons'].append('Identical content to '+seen[item['sha256']]);inventory.append(row);continue
        seen[item['sha256']]=item['name']
        try:
            doc=inspect(item['name'],item['bytes'])
            acra=extract_acra_profile(doc) if item['name'].lower().endswith('.pdf') else dict(detected=False,fields={})
            bank=extract_bank_statement(doc)
        except Exception as exc:
            row['reasons'].append(str(exc));inventory.append(row);continue
        row['demo']=demonstration(doc)
        row['company']=acra.get('fields',{}).get('company_name') or company_name(doc)
        row['authenticity']='synthetic_fixture' if row['demo'] else 'unverified_original'
        if row['demo'] and not synthetic_test_mode:
            row.update(type='Demonstration / fictional document',status='Excluded from bank evidence')
            row['reasons'].append('Synthetic evidence cannot establish actual bank coverage. Enable Synthetic Test Mode in a new workspace to test it.')
        elif synthetic_test_mode and not row['demo'] and (acra.get('detected') or bank.get('detected')):
            row.update(type='Original-looking source',status='Excluded from synthetic test workspace')
            row['reasons'].append('Only explicitly labelled synthetic bank/profile fixtures are allowed in Synthetic Test Mode.')
        else:
            if row['demo']:
                row['reasons'].append('SYNTHETIC TEST ONLY: this fixture is not authentic company or bank evidence.')
            if acra.get('detected') and acra.get('fields'):
                row.update(type='Company profile',status='Synthetic test profile — review fields' if row['demo'] else 'Review proposed company fields')
                mismatch=(config.get('uen') and acra['fields'].get('uen') and config['uen'].strip().upper()!=acra['fields']['uen'].strip().upper())
                mismatch=mismatch or (expected and row['company'] and expected!=canonical_name(row['company']))
                if mismatch:
                    row['status']='Excluded company mismatch'
                    row['reasons'].append('Company profile does not match this workspace.')
                for key,value in ({} if mismatch else acra['fields']).items():
                    row['fields'].append(provenance(doc,value,key));proposals[key].append(row['fields'][-1])
            elif bank.get('detected'):
                row.update(type='Bank statement',status='Synthetic test statement — not authentic evidence' if row['demo'] else 'Review statement')
                row['bank']=bank
                if row['company']:
                    proposals['company_name'].append(provenance(doc,row['company'],'company_name'))
                if expected and row['company'] and canonical_name(row['company'])!=expected:
                    row['status']='Excluded company mismatch';row['reasons'].append('Account holder differs from the current company.')
                elif not bank.get('account_id'):
                    row['reasons'].append('Account number missing: cannot group or import safely.')
                else:
                    for key in ('opening','closing','period_start','period_end'):
                        if bank.get(key) is not None:row['fields'].append(provenance(doc,bank[key],key))
                    groups[bank['account_id']].append((doc,acra,bank,row))
                row['reasons'].extend(bank.get('warnings',[]))
            else:
                row.update(type='Supporting record / template',status='Retained for manual mapping')
                row['reasons'].extend(doc.notes)
        parsed.append((doc,acra,bank));inventory.append(row)
    accounts=[]
    for key,items in sorted(groups.items()):
        names={canonical_name(row['company']) for _,_,_,row in items if row['company']}
        mixed=len(names)>1
        cov=coverage([b for _,_,b,_ in items],config.get('fy_start') if config.get('fy_confirmed') else None,
                     config.get('fy_end') if config.get('fy_confirmed') else None)
        if mixed:
            cov['balances']['ready']=False;cov['balances']['errors'].append('Conflicting account-holder names; review company identity.')
        accounts.append(dict(id=key, label=items[0][2].get('masked_account'), bank=items[0][2].get('bank'),
                             company=items[0][3]['company'], coverage=cov,
                             sources=[row['id'] for _,_,_,row in items], mixed=mixed))
    agreed={}
    for key,values in proposals.items():
        normalise=canonical_name if key=='company_name' else lambda v:str(v).strip().upper()
        if len({normalise(p['value']) for p in values})==1:agreed[key]=values[0]
    return dict(inventory=inventory,parsed=parsed,accounts=accounts,proposals=agreed,
                context=digest({k:config.get(k) for k in ('company_name','uen','fy_start','fy_end','fy_confirmed','synthetic_test_mode')}),
                conflicts=[k for k in proposals if k not in agreed],
                fingerprint=digest([(r['id'],r['sha256']) for r in inventory]))


def bank_proposal(analysis, config, existing):
    """One supported bank ledger, current-period rows only, fail closed on ambiguity."""
    errors=[];rows=[];sources=[]
    if 'bank_accounts' in config:
        errors.append('Use account-by-account review for this multi-bank workspace; legacy import is blocked.')
    if analysis['context']!=digest({k:config.get(k) for k in ('company_name','uen','fy_start','fy_end','fy_confirmed','synthetic_test_mode')}):
        errors.append('Setup changed after analysis; analyse the sources again.')
    if not (config.get('fy_confirmed') and config.get('company_name') and config.get('uen')):
        errors.append('Confirm company identity and reporting dates.')
    if len(analysis['accounts'])!=1:
        errors.append('Auto posting currently supports exactly one bank account; keep other accounts separate for review.')
    acceptable={r['sha256']:r for r in analysis['inventory'] if r.get('type')=='Bank statement' and r.get('status')!='Excluded company mismatch'}
    if any(r.get('status')=='Excluded company mismatch' for r in analysis['inventory']):
        errors.append('Remove statements belonging to another company before importing.')
    low,high=_date(config.get('fy_start')),_date(config.get('fy_end'))
    for doc,acra,b in analysis['parsed']:
        if doc.sha256 not in acceptable or not b.get('detected'):continue
        row=acceptable[doc.sha256]
        from .bank_intake import identify
        currency=identify(doc)['currency']
        if currency not in (None,'SGD'):
            errors.append(doc.name+': only SGD statement currency is supported.');continue
        if not row.get('company') or canonical_name(row['company'])!=canonical_name(config.get('company_name')):
            errors.append(doc.name+': account holder could not be matched to the confirmed company.');continue
        start,end=_date(b.get('period_start')),_date(b.get('period_end'))
        if not start or not end:
            errors.append(doc.name+': statement period needs review.');continue
        if not low or not high:continue
        if end<low or start>high:continue  # Opening/comparative evidence never posts current-year transactions.
        proposed,warnings=propose_bank_rows(doc)
        errors.extend(doc.name+': '+w for w in warnings)
        if not proposed:errors.append(doc.name+': no reliable transaction rows; use a bank CSV/Excel export or Advanced mapping.')
        if any(not low<=_date(r['date'])<=high for r in proposed):errors.append(doc.name+': rows outside the reporting period.')
        if b.get('opening') is None or b.get('closing') is None:
            errors.append(doc.name+': balance amounts are missing.')
        elif sum((Decimal(r['deposit'] or '0')-Decimal(r['withdrawal'] or '0') for r in proposed),Decimal('0'))!=Decimal(b['closing'])-Decimal(b['opening']):
            errors.append(doc.name+': transaction totals do not tie to the statement movement.')
        rows.extend(dict(r,account_code='9999') for r in proposed)
        sources.append(dict(source=doc.name,sha256=doc.sha256))
    for account in analysis['accounts']:errors.extend(account['coverage']['balances']['errors'])
    if existing_duplicates([],rows,'bank'):errors.append('Potential duplicate transaction rows need review.')
    if existing:
        errors.append('The ledger already contains bank transactions. Auto full-period import is blocked; use Advanced review for additional or corrected rows.')
    if existing_duplicates(existing,rows,'bank'):errors.append('These proposals overlap previously recorded transactions; import is blocked.')
    if not rows:errors.append('No current-period transactions are ready to import.')
    return dict(rows=rows,errors=list(dict.fromkeys(errors)),sources=sources,
                id=digest(dict(rows=rows,sources=sources,company=config.get('uen'),start=config.get('fy_start'),end=config.get('fy_end'))))


def approve_bank(pkg, analysis, proposal_id, approved=False):
    proposal=bank_proposal(analysis,pkg.config,pkg.bank)
    if not approved or proposal['id']!=proposal_id or proposal['errors']:
        return False
    # User reviewed the exact current proposal. Persist enough metadata to detect stale approvals.
    pkg.bank.extend(deepcopy(proposal['rows']))
    pkg.config.setdefault('auto_imports',[]).append(dict(id=proposal_id,sources=proposal['sources'],row_count=len(proposal['rows'])))
    pkg.config['bank_balances_confirmed']=False
    return True
