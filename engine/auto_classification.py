"""Treat external AI suggestions as untrusted proposals for exact ledger rows."""
from .auto import digest
from .core import COA_MAP


def bank_revision(bank):
    columns=('date','description','reference','deposit','withdrawal','account_code','evidence_ref','notes')
    return digest([{k:str(row.get(k) or '') for k in columns} for row in bank])


def validate_proposals(bank, payload):
    if not isinstance(payload,dict) or payload.get('ledger_revision')!=bank_revision(bank):
        raise ValueError('Suggestions refer to a different ledger revision. Export a fresh review request.')
    suggestions=payload.get('suggestions')
    if not isinstance(suggestions,list) or len(suggestions)>len(bank):
        raise ValueError('Invalid suggestions list.')
    seen=set();validated=[]
    for s in suggestions:
        if not isinstance(s,dict):raise ValueError('Invalid suggestion.')
        idx=s.get('row');code=s.get('account_code');confidence=s.get('confidence');reason=s.get('reason')
        if type(idx) is not int or idx<0 or idx>=len(bank) or idx in seen:
            raise ValueError('Invalid or repeated transaction row.')
        if code not in COA_MAP or code in ('1000','9999'):
            raise ValueError('Unsupported category suggestion.')
        if type(confidence) not in (int,float) or not 0<=confidence<=1:
            raise ValueError('Confidence must be a number from 0 to 1.')
        if not isinstance(reason,str) or not reason.strip() or len(reason)>1000:
            raise ValueError('Every suggestion requires a short explanation.')
        ref=bank[idx].get('evidence_ref','')
        if not ref or s.get('source_ref')!=ref:
            raise ValueError('Suggestion must link to the transaction source reference.')
        seen.add(idx);validated.append(dict(row=idx,account_code=code,confidence=confidence,reason=reason,source_ref=ref))
    return validated


def apply_categories(pkg, revision, codes):
    if revision!=bank_revision(pkg.bank) or len(codes)!=len(pkg.bank):
        return False
    if any(code not in COA_MAP or code=='1000' for code in codes):
        return False
    before=[row.get('account_code') for row in pkg.bank]
    if before==codes:return False
    for row,code in zip(pkg.bank,codes):row['account_code']=code
    pkg.config.setdefault('auto_category_history',[]).append(dict(
        id=digest(dict(before=revision,codes=codes)), before=revision, after=bank_revision(pkg.bank),
        previous_codes=before, approved_codes=list(codes), source='Human reviewed proposals',reverted=False))
    return True


def revert_categories(pkg, record_id):
    record=next((r for r in reversed(pkg.config.get('auto_category_history',[])) if r['id']==record_id),None)
    if not record or record.get('reverted') or record['after']!=bank_revision(pkg.bank):
        return False
    if len(record.get('previous_codes',[]))!=len(pkg.bank):return False
    for row,code in zip(pkg.bank,record['previous_codes']):row['account_code']=code
    record['reverted']=True
    return True
