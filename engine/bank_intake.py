"""Review-first bank identification, account grouping and per-account coverage.

Source documents are untrusted data. No account, transaction or transfer is
created by analysis. Only explicit review APIs mutate a workspace.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
from hashlib import sha256
import re
from .importers import inspect_document
from .autofill import (extract_bank_statement,consolidate_statement_balances,propose_bank_rows,DATE_RX,_date)
from .multi_bank import fingerprint,row_facts,pair_hash
from .bank_headers import header_lines,account_holder

MAX_FILES=50
MAX_BYTES=100*1024*1024


def context(config):
    return fingerprint({k:config.get(k) for k in ('company_name','uen','fy_start','fy_end','fy_confirmed','currency')})


def name_key(name):return re.sub('[^A-Z0-9]','',str(name or '').upper())


def _date_value(text):
    try:return date.fromisoformat(text)
    except (ValueError,TypeError):return None


def _source_lines(doc):
    lines=doc.text_excerpt.splitlines()
    if not lines:lines=[' '.join(row) for t in doc.tables for row in t.rows[:40]]
    return [re.sub(r'\s+',' ',line).strip() for line in lines if line.strip()]


def _location(doc,text):
    for idx,page in enumerate(getattr(doc,'text_pages',()),1):
        if text and re.sub(r'\s+',' ',text).strip() in re.sub(r'\s+',' ',page):return idx
    return None


def identify(doc):
    lines=_source_lines(doc);head=header_lines(doc)
    bank_patterns={'OCBC':r'^(?:Bank\s*[:|]?\s*)?(?:OCBC\b|OVERSEA-CHINESE\s+BANKING)',
                   'DBS':r'^(?:Bank\s*[:|]?\s*)?(?:DBS\b|DEVELOPMENT\s+BANK\s+OF\s+SINGAPORE)',
                   'UOB':r'^(?:Bank\s*[:|]?\s*)?(?:UOB\b|UNITED\s+OVERSEAS\s+BANK)'}
    banks={bank for bank,rx in bank_patterns.items() if any(re.search(rx,re.sub(r'^.*?\bBIC Name\s+','',line,flags=re.I),re.I) for line in head)}
    errors=[];locations=[]
    bank=next(iter(banks)) if len(banks)==1 else ''
    if not bank:errors.append('Bank identity is missing, unsupported or ambiguous; review the original.')
    accounts=[]
    rx=r'\b(?:Account\s*(?:Number|No\.?)|A/C(?:\s*(?:Number|No\.?))?)\s*[:#|]?\s*([0-9][0-9 -]{4,28}[0-9])\b'
    for line in head:
        for match in re.finditer(rx,line,re.I):
            normal=re.sub(r'\D','',match.group(1))
            if 6<=len(normal)<=24:accounts.append((normal,line,match.group(1)))
    unique={number for number,_,_ in accounts}
    account=next(iter(unique)) if len(unique)==1 else ''
    if not account:errors.append('Full account number is missing or ambiguous; masked suffixes are not enough to group accounts.')
    currencies=set()
    for line in head:
        match=re.search(r'\b(?:Account\s+|Statement\s+)?(?:Currency|CCY)\s*[:|]?\s*(SGD|USD|EUR|GBP|AUD|JPY|CNH|CNY|HKD|MYR)\b',line,re.I)
        if match:currencies.add(match.group(1).upper())
        if re.search(r'\bSGD\s+(?:CURRENT|SAVINGS|BUSINESS|ACCOUNT)\b|\bACCOUNT\b.*\(SGD\)',line,re.I):currencies.add('SGD')
    for line in head:
        match=re.match(r'^Account Number\s+[\d -]+\s*-\s*([A-Z]{3})\b',line,re.I)
        if match:currencies.add(match.group(1).upper())
    currency=next(iter(currencies)) if len(currencies)==1 else None
    if len(currencies)>1:errors.append('Conflicting statement currencies; do not combine currency subaccounts.')
    if currency and currency!='SGD':errors.append('Only SGD account statements are supported.')
    holder=account_holder(doc);owner=holder['value'];errors.extend(holder['errors'])
    summary=extract_bank_statement(doc)
    periods=set()
    period_rx=r'^(?:(?:Statement\s+Period(?:\s+From)?|Period\s+Covered|For\s+the\s+Period|Period\s+From|From|BUSINESS\s+GROWTH\s+ACCOUNT|CURRENT\s+ACCOUNT|BUSINESS\s+ACCOUNT|UOB\s+BIZTRANS\s+ACCOUNT)\s*[:|]?\s*)?('+DATE_RX+r')\s*(?:TO|THROUGH|UNTIL|–|—|\s-\s)\s*('+DATE_RX+r')$'
    for line in head:
        match=re.match(period_rx,line,re.I)
        if match:
            a,b=_date(match.group(1)),_date(match.group(2))
            if a and b and a<=b:periods.add((a,b))
            else:errors.append('Invalid statement period.')
    if len(periods)==1:
        summary['period_start'],summary['period_end']=next(iter(periods))
        if summary.get('daily_profile'):
            summary['period_end']=summary.get('coverage_verified_through')
            errors.extend(summary.get('warnings',[]))
    else:
        summary['period_start']=summary['period_end']=None
        errors.append('Explicit statement period is missing or conflicting; filenames and statement dates do not prove coverage.')
    if summary.get('opening') is None or summary.get('closing') is None:errors.append('Opening/closing balance cannot be read unambiguously.')
    if any(re.search(r'^(?:Opening\s+Balance|Closing\s+Balance|Balance\s+[BC]\s*/\s*F).*\b(?:DR|OD|OVERDRAWN)\b',line,re.I) for line in head):
        errors.append('Debit/overdraft balance notation needs manual review; overdrafts are not supported.')
    if any(Decimal(summary[k])<0 for k in ('opening','closing') if summary.get(k) is not None):errors.append('Overdraft presentation is not supported.')
    demo=bool(re.search(r'\b(?:FICTIONAL|SYNTHETIC|DEMONSTRATION|DEMO|NOT[ -]+OFFICIAL|NOT[ -]+REAL)\b',(doc.name+' '+doc.text_excerpt).replace('_',' '),re.I))
    if demo:errors.append('Fictional/demonstration evidence cannot establish actual bank coverage.')
    account_key=sha256((bank+'\0'+account).encode()).hexdigest() if bank and account else ''
    masked='••••'+account[-4:] if account else 'Not identified'
    for key,value in (('bank',bank),('account',masked),('currency',currency),('company',owner),('period_start',summary.get('period_start')),('period_end',summary.get('period_end')),('opening',summary.get('opening')),('closing',summary.get('closing'))):
        line=next((line for line in head if str(value or '').upper() in line.upper() and value),None)
        if key=='account' and account:
            entry=next(a for a in accounts if a[0]==account);line=entry[1];snippet=line.replace(entry[2],masked)
        else:snippet=line
        if key in ('period_start','period_end') and not line:
            line=next((line for line in head if re.match(period_rx,line,re.I)),None);snippet=line
        if key in ('opening','closing'):
            line=next((line for line in lines if re.search(r'Opening|Brought|B/F' if key=='opening' else r'Closing|Carried|C/F|Ledger Balance',line,re.I)),None);snippet=line
        for _,_,raw_number in accounts:
            if snippet:snippet=snippet.replace(raw_number,masked)
        locations.append(dict(field=key,value=value,page=_location(doc,line) if line else None,excerpt=(snippet or '')[:250],sha256=doc.sha256))
    summary.update(detected=bool(bank and account),bank=bank,account_id=account_key,masked_account=masked,sha256=doc.sha256,source=doc.name)
    return dict(name=doc.name,sha256=doc.sha256,bank=bank,account_key=account_key,masked_account=masked,currency=currency,
                company=owner,demo=demo,errors=list(dict.fromkeys(errors)),summary=summary,provenance=locations)


def _coverage(summaries,config):
    low,high=_date_value(config.get('fy_start')),_date_value(config.get('fy_end'))
    current=[];outside=[];months=[];errors=[]
    if not low or not high or low>high or (high-low).days>732:return dict(ready=False,errors=['Confirm valid reporting dates.'],months=[],current=[],outside=[],opening=None,closing=None)
    for summary in summaries:
        start,end=_date_value(summary.get('period_start')),_date_value(summary.get('period_end'))
        if start and end and (end<low or start>high):outside.append(summary)
        else:current.append(summary)
    answer=consolidate_statement_balances(current,str(low),str(high))
    cursor=low.replace(day=1)
    from calendar import monthrange
    while cursor<=high:
        left=max(low,cursor);right=min(high,cursor.replace(day=monthrange(cursor.year,cursor.month)[1]));upto=left.toordinal()
        spans=sorted((max(left,_date_value(s['period_start'])),min(right,_date_value(s['period_end']))) for s in current
                     if _date_value(s.get('period_start')) and _date_value(s.get('period_end')) and _date_value(s['period_start'])<=right and _date_value(s['period_end'])>=left)
        for a,b in spans:
            if a.toordinal()>upto:break
            upto=max(upto,b.toordinal()+1)
        months.append(dict(month=cursor.strftime('%Y-%m'),status='Covered' if upto>right.toordinal() else 'Missing / incomplete'))
        if cursor.year==9999 and cursor.month==12:break
        cursor=(cursor.replace(day=28)+timedelta(days=4)).replace(day=1)
    for prior in outside:
        if low>date.min and _date_value(prior.get('period_end'))==low-timedelta(days=1) and prior.get('closing') is not None and answer.get('opening') is not None and Decimal(prior['closing'])!=Decimal(answer['opening']):
            errors.append('Previous-period closing conflicts with current opening evidence.')
    errors+=answer['errors']
    return dict(ready=not errors,errors=errors,months=months,current=current,outside=outside,opening=answer.get('opening'),closing=answer.get('closing'))


def analyse_documents(files,config,inspect=inspect_document):
    if len(files)>MAX_FILES or sum(len(f['bytes']) for f in files)>MAX_BYTES:raise ValueError('Batch limit: 50 files / 100 MB.')
    inventory=[];groups=defaultdict(list);documents={};seen={}
    for f in files:
        actual=sha256(f['bytes']).hexdigest()
        if actual!=f['sha256']:raise ValueError('File fingerprint mismatch.')
        if actual in seen:
            inventory.append(dict(name=f['name'],sha256=actual,status='Excluded exact duplicate',errors=['Identical content to '+seen[actual]],provenance=[]));continue
        seen[actual]=f['name']
        try:
            doc=inspect(f['name'],f['bytes']);row=identify(doc);documents[actual]=doc
            row['status']='Needs review' if row['errors'] else 'Identified - reviewer confirmation required'
            if row['account_key'] and not row['demo']:groups[row['account_key']].append(row)
        except Exception as exc:row=dict(name=f['name'],sha256=actual,status='Unreadable / unsupported',errors=[str(exc)],provenance=[])
        inventory.append(row)
    results=[]
    for key,rows in sorted(groups.items()):
        rows=sorted(rows,key=lambda r:(r['summary'].get('period_start') or '',r['sha256']))
        errors=[r['name']+': '+e for r in rows for e in r['errors']]
        names={name_key(r['company']) for r in rows if r['company']}
        if len(names)>1:errors.append('Account-holder names conflict within this statement group.')
        expected=name_key(config.get('company_name'))
        if expected and any(n!=expected for n in names):errors.append('Statement company differs from the current workspace.')
        currencies={r['currency'] for r in rows if r['currency']}
        if len(currencies)>1:errors.append('Mixed currencies cannot share a ledger account.')
        cov=_coverage([r['summary'] for r in rows],config);errors+=cov['errors']
        group=dict(key=key,bank=rows[0]['bank'],masked_account=rows[0]['masked_account'],currency=next(iter(currencies)) if len(currencies)==1 else None,
                   company=rows[0]['company'],sources=rows,coverage=cov,errors=list(dict.fromkeys(errors)))
        group['revision']=fingerprint(dict(context=context(config),sources=[r['summary'] for r in rows],currency=group['currency'],company=group['company'],errors=group['errors']))
        results.append(group)
    return dict(context=context(config),inventory=inventory,groups=results,documents=documents)


def coverage_payload(meta,config):
    return dict(context=context(config),code=str(meta.get('code')),account_key=meta.get('account_key'),currency=meta.get('currency'),
                opening=str(meta.get('opening')),closing=str(meta.get('closing')),statements=meta.get('statements',[]))


def validate_managed_account(meta,config):
    if not meta.get('managed_intake'):return []
    from .core import money
    errors=[];record=meta.get('coverage_review') or {}
    if not isinstance(record,dict):return ['Invalid saved source coverage review; re-analyse originals.']
    if not record.get('reviewer') or not record.get('evidence') or record.get('hash')!=fingerprint(coverage_payload(meta,config)):
        errors.append('Automated source coverage approval is missing or stale; re-analyse and review.')
    summaries=meta.get('statements',[])
    if not isinstance(summaries,list) or any(not isinstance(s,dict) for s in summaries):return errors+['Invalid saved statement summaries; re-analyse originals.']
    for summary in summaries:
        low,high=_date_value(summary.get('period_start')),_date_value(summary.get('period_end'))
        if not low or not high or low>high:return errors+['Invalid saved statement dates; re-analyse originals.']
        try:
            for key in ('opening','closing'):
                if summary.get(key) is None or money(summary[key])<0:raise ValueError()
        except (ValueError,TypeError):return errors+['Invalid saved statement balances; re-analyse originals.']
    if not summaries or any(s.get('account_id')!=meta.get('account_key') for s in summaries):errors.append('Saved source identity does not match the registered bank.')
    else:
        cov=_coverage(summaries,config);errors.extend(cov['errors'])
        if cov['opening']!=meta.get('opening') or cov['closing']!=meta.get('closing'):errors.append('Registered balances differ from source coverage.')
    return errors


def approve_account(pkg,analysis,key,code,revision,reviewer,evidence,confirmed=False,link_existing=False):
    if not confirmed or not reviewer.strip() or not evidence.strip() or analysis['context']!=context(pkg.config) or not pkg.config.get('company_name') or not pkg.config.get('uen') or not pkg.config.get('fy_confirmed'):return False
    group=next((g for g in analysis['groups'] if g['key']==key),None)
    if not group or group['revision']!=revision or group['errors'] or not group['coverage']['ready'] or group['currency'] not in (None,'SGD'):return False
    if not re.fullmatch(r'10[0-9]{2}',str(code)) or 'bank_accounts' not in pkg.config:return False
    old=next((r for r in pkg.config['bank_accounts'] if str(r.get('code'))==str(code)),None)
    if any(r.get('account_key')==key and str(r.get('code'))!=str(code) for r in pkg.config['bank_accounts']):return False
    if old and old.get('account_key') and old['account_key']!=key:return False
    if old and not old.get('account_key') and any(str(r.get('bank_account_code'))==str(code) for r in pkg.bank) and not link_existing:return False
    meta=dict(old or {},code=str(code),name=(old or {}).get('name') or group['bank']+' '+group['masked_account'],currency='SGD',
              bank=group['bank'],account_key=key,masked_account=group['masked_account'],opening=group['coverage']['opening'],closing=group['coverage']['closing'],
              confirmed=True,coverage_confirmed=True,managed_intake=True,statements=deepcopy([r['summary'] for r in group['sources']]))
    meta['coverage_review']=dict(reviewer=reviewer.strip(),evidence=evidence.strip(),at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
        hash=fingerprint(coverage_payload(meta,pkg.config)),method='Source identification and exact per-account coverage; currency/company confirmed by reviewer')
    # Source changes require fresh transaction evidence review.
    if not old or old.get('coverage_review',{}).get('hash')!=meta['coverage_review']['hash']:meta.pop('transactions_review',None)
    values=[deepcopy(r) for r in pkg.config['bank_accounts'] if str(r.get('code'))!=str(code)]+[meta]
    if old and old.get('coverage_review') and old['coverage_review']!=meta['coverage_review']:
        pkg.config.setdefault('bank_review_history',[]).append(dict(code=str(code),kind='coverage',record=deepcopy(old['coverage_review'])))
    if old and old.get('transactions_review') and 'transactions_review' not in meta:
        pkg.config.setdefault('bank_review_history',[]).append(dict(code=str(code),kind='transactions',record=deepcopy(old['transactions_review'])))
    pkg.config['bank_accounts']=sorted(values,key=lambda r:r['code'])
    return True


def account_row_hash(rows,code):
    return fingerprint(sorted([row_facts(r) for r in rows if str(r.get('bank_account_code'))==str(code)],key=lambda r:(r['date'],r['reference'])))


def review_recorded_rows(pkg,code,reviewer,evidence,confirmed=False):
    """Explicit original-source review for existing/manual rows; never called by analysis."""
    from .core import money,parse_date
    meta=next((m for m in pkg.config.get('bank_accounts',[]) if m.get('code')==str(code)),None)
    if not confirmed or not reviewer.strip() or not evidence.strip() or not meta or not meta.get('managed_intake') or validate_managed_account(meta,pkg.config):return False
    rows=[r for r in pkg.bank if str(r.get('bank_account_code'))==str(code)]
    try:
        low,high=parse_date(pkg.config['fy_start']),parse_date(pkg.config['fy_end'])
        for r in rows:
            if not low<=parse_date(r['date'])<=high or not r.get('reference') or not r.get('evidence_ref'):return False
            dep,wd=money(r.get('deposit')),money(r.get('withdrawal'))
            if dep<0 or wd<0 or (dep>0)==(wd>0):return False
        movement=sum((money(r.get('deposit'))-money(r.get('withdrawal')) for r in rows),Decimal('0'))
        if money(meta['opening'])+movement!=money(meta['closing']):return False
    except (ValueError,KeyError,TypeError):return False
    if meta.get('transactions_review'):
        pkg.config.setdefault('bank_review_history',[]).append(dict(code=str(code),kind='transactions',record=deepcopy(meta['transactions_review'])))
    meta['transactions_review']=dict(reviewer=reviewer.strip(),evidence=evidence.strip(),hash=account_row_hash(pkg.bank,code),
         coverage_hash=meta['coverage_review']['hash'],method='Manual original-source transaction review',at=datetime.now(timezone.utc).isoformat(timespec='seconds'))
    return True


def transaction_review_errors(meta,config,rows):
    if not meta.get('managed_intake'):return []
    record=meta.get('transactions_review') or {}
    if not isinstance(record,dict):return ['Invalid saved transaction review; review the original rows.']
    if not record.get('reviewer') or not record.get('evidence') or record.get('hash')!=account_row_hash(rows,meta['code']) or record.get('coverage_hash')!=meta.get('coverage_review',{}).get('hash'):
        return ['Source transaction review is missing or stale; reconcile and review the original statement rows.']
    return []


def staged_rows(pkg,analysis,key):
    from .core import money
    group=next((g for g in analysis['groups'] if g['key']==key),None)
    meta=next((m for m in pkg.config.get('bank_accounts',[]) if m.get('account_key')==key),None)
    errors=[];rows=[]
    if not group or not meta:return dict(rows=[],errors=['Review and assign this statement group to a bank account first.'],revision='')
    if analysis['context']!=context(pkg.config):errors.append('Company/period changed; re-analyse source files.')
    errors.extend(group['errors'])
    errors.extend(validate_managed_account(meta,pkg.config))
    if [r['summary'] for r in group['sources']]!=meta.get('statements'):errors.append('Statement set changed; approve current source coverage before staging rows.')
    imported=set(pkg.config.get('bank_source_imports',{}).get(meta['code'],[]))
    for summary in group['coverage']['current']:
        if summary['sha256'] in imported:continue
        doc=analysis['documents'].get(summary['sha256'])
        if doc is None:errors.append('Original source is unavailable: '+summary['source']);continue
        proposed,warnings=propose_bank_rows(doc)
        errors.extend(doc.name+': '+str(w) for w in warnings)
        if not proposed and money(summary.get('opening'))!=money(summary.get('closing')):
            errors.append(doc.name+': no reliable transaction rows; use manual mapping/review.')
        net=sum((money(r.get('deposit'))-money(r.get('withdrawal')) for r in proposed),Decimal('0'))
        if summary.get('opening') is None or summary.get('closing') is None or money(summary['opening'])+net!=money(summary['closing']):
            errors.append(doc.name+': extracted transactions do not tie to statement movement.')
        for idx,r in enumerate(proposed,1):
            if not summary['period_start']<=r['date']<=summary['period_end']:errors.append(doc.name+': row date is outside its statement period.')
            row=dict(r,bank_account_code=meta['code'],account_code='9999',transfer_id='',source_sha256=doc.sha256,
                     source_row=str(idx),source_reference=str(r.get('source_reference') or r.get('reference') or ''),reference='SRC-'+doc.sha256[:16]+'-'+str(idx),
                     evidence_ref='DOC-'+doc.sha256[:12].upper())
            rows.append(row)
    old={str(r.get('reference')) for r in pkg.bank if str(r.get('bank_account_code'))==meta['code']}
    if any(r['reference'] in old for r in rows):errors.append('A proposed source row was already recorded; do not duplicate it.')
    if any(str(r.get('bank_account_code'))==meta['code'] and not r.get('source_sha256') for r in pkg.bank) and rows:
        errors.append('This account has manually recorded rows. Review existing rows against sources instead of appending a statement batch.')
    revision=fingerprint(dict(context=context(pkg.config),group=group['revision'],existing=account_row_hash(pkg.bank,meta['code']),rows=rows,errors=errors))
    return dict(rows=rows,errors=list(dict.fromkeys(errors)),revision=revision)


def approve_import(pkg,analysis,key,revision,reviewer,evidence,confirmed=False):
    proposal=staged_rows(pkg,analysis,key)
    if not confirmed or not reviewer.strip() or not evidence.strip() or proposal['revision']!=revision or proposal['errors'] or not proposal['rows']:return False
    # Work on a copy so all rejection paths preserve original books and review metadata.
    candidate=deepcopy(pkg);meta=next(m for m in candidate.config['bank_accounts'] if m.get('account_key')==key)
    candidate.bank.extend(deepcopy(proposal['rows']))
    hashes=sorted({r['source_sha256'] for r in proposal['rows']})
    prior=candidate.config.setdefault('bank_source_imports',{}).setdefault(meta['code'],[])
    prior.extend(h for h in hashes if h not in prior)
    for row in proposal['rows']:
        ref=row['evidence_ref']
        if not any(e.get('evidence_ref')==ref for e in candidate.evidence):
            name=next(g['summary']['source'] for group in analysis['groups'] for g in group['sources'] if g['sha256']==row['source_sha256'])
            candidate.evidence.append(dict(evidence_ref=ref,document_type='Bank statement',source_file=name,review_status='Reviewed',remarks='Reviewer '+reviewer.strip()+'; SHA-256 '+row['source_sha256']))
    if not review_recorded_rows(candidate,meta['code'],reviewer,evidence,True):return False
    candidate.config.setdefault('bank_import_reviews',[]).append(dict(revision=revision,code=meta['code'],source_hashes=hashes,reviewer=reviewer.strip(),evidence=evidence.strip(),count=len(proposal['rows'])))
    pkg.config=candidate.config;pkg.bank=candidate.bank;pkg.evidence=candidate.evidence
    return True


def suggest_transfers(pkg):
    from .core import money,parse_date
    rows=pkg.bank;accounts={m['code'] for m in pkg.config.get('bank_accounts',[]) if m.get('currency')=='SGD'}
    incoming=[];outgoing=[]
    for idx,row in enumerate(rows):
        if row.get('transfer_id') or str(row.get('account_code') or '9999') not in ('','9999','TRANSFER') or row.get('bank_account_code') not in accounts:continue
        try:
            dep,wd=money(row.get('deposit')),money(row.get('withdrawal'));dt=parse_date(row.get('date'))
            if dep<0 or wd<0 or (dep>0)==(wd>0) or not pkg.config['fy_start']<=str(dt)<=pkg.config['fy_end']:continue
            if not row.get('reference') or not row.get('evidence_ref'):continue
            (incoming if dep>0 else outgoing).append((idx,dt,dep if dep>0 else wd))
        except (ValueError,KeyError,TypeError):continue
    candidates=[];counts=defaultdict(int)
    for out,dt,amount in outgoing:
        for inc,other_dt,other_amount in incoming:
            if dt==other_dt and amount==other_amount and rows[out]['bank_account_code']!=rows[inc]['bank_account_code']:
                token=fingerprint(dict(context=context(pkg.config),rows=sorted([row_facts(rows[out]),row_facts(rows[inc])],key=lambda r:(r['bank_account_code'],r['reference']))))
                candidates.append(dict(id=token,out_reference=rows[out]['reference'],in_reference=rows[inc]['reference'],
                    out_account=rows[out]['bank_account_code'],in_account=rows[inc]['bank_account_code'],date=str(dt),amount=str(amount),
                    basis='Same date and equal opposite SGD amount; original evidence must establish an internal transfer.',out_index=out,in_index=inc))
                counts[out]+=1;counts[inc]+=1
    for c in candidates:c['ambiguous']=counts[c['out_index']]>1 or counts[c['in_index']]>1
    return candidates


def approve_transfer(pkg,candidate_id,reviewer,evidence,confirmed=False):
    if not confirmed or not reviewer.strip() or not evidence.strip():return False
    candidate=next((c for c in suggest_transfers(pkg) if c['id']==candidate_id),None)
    if not candidate or candidate['ambiguous']:return False
    rows=deepcopy(pkg.bank);a,b=rows[candidate['out_index']],rows[candidate['in_index']]
    tid='RV-'+candidate_id[:20].upper()
    a.update(account_code='TRANSFER',transfer_id=tid);b.update(account_code='TRANSFER',transfer_id=tid)
    review=dict(reviewer=reviewer.strip(),evidence=evidence.strip(),pair_hash=pair_hash(a,b),context=context(pkg.config),at=datetime.now(timezone.utc).isoformat(timespec='seconds'),method='Explicit approval of a unique source-matched suggestion')
    # Approval affects categories and links only. Amounts, dates and original source identities are untouched.
    prior=pkg.config.setdefault('transfer_reviews',{}).get(tid)
    if prior:pkg.config.setdefault('bank_review_history',[]).append(dict(code=tid,kind='transfer',record=deepcopy(prior)))
    pkg.bank=rows;pkg.config['transfer_reviews'][tid]=review
    return True


def apply_registry(pkg,edits):
    """Preserve intake/review metadata; do not orphan posted bank accounts."""
    from .multi_bank import registry
    from .core import COA_MAP
    old={str(m.get('code')):m for m in pkg.config.get('bank_accounts',[])}
    used={str(r.get('bank_account_code')) for r in pkg.bank}|{str(r.get('account_code')) for r in pkg.journals if str(r.get('account_code')) in old}
    codes={str(r.get('code','')).strip() for r in edits}
    if used-codes:return False
    values=[]
    for row in edits:
        code=str(row.get('code','')).strip();meta=dict(old.get(code,{}),**row);meta['code']=code
        if code in old and any(str(old[code].get(k,''))!=str(meta.get(k,'')) for k in ('opening','closing','currency')):
            meta['confirmed']=meta['coverage_confirmed']=False
        values.append(meta)
    errors=[];registry(dict(pkg.config,bank_accounts=values),COA_MAP,errors)
    # Unconfirmed data may be saved for correction; invalid registry structure/currency may not replace valid data.
    if any('explicit review' not in e for e in errors):return False
    pkg.config['bank_accounts']=values
    return True
