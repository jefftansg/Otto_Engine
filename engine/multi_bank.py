"""Reviewed SGD bank registry and explicit same-date transfer pairs.

Pure helpers; no mutation of the global chart of accounts or source records.
"""
import re
from copy import deepcopy
from hashlib import sha256
import json
from collections import defaultdict
from decimal import Decimal


def registry(config, base_coa, errors):
    """Return an isolated COA and validated bank metadata for this workspace."""
    coa = deepcopy(base_coa)
    if 'bank_accounts' not in config:
        return coa, None
    accounts = config['bank_accounts']
    registered = {}
    if not isinstance(accounts, list) or not accounts:
        errors.append('Multi-bank mode requires at least one registered SGD bank account.')
        return coa, registered
    for row in accounts:
        if not isinstance(row, dict):
            errors.append('Invalid bank registry entry.')
            continue
        code = str(row.get('code', '')).strip()
        name = str(row.get('name', '')).strip()
        if not re.fullmatch(r'10[0-9]{2}', code) or code in registered or not name:
            errors.append('Bank registry: invalid or duplicate code/name; use unique codes 1000–1099.')
            continue
        if row.get('currency') != 'SGD':
            errors.append(f'Bank {code}: only SGD accounts are supported.')
            continue
        if row.get('confirmed') is not True or row.get('coverage_confirmed') is not True:
            errors.append(f'Bank {code}: statement balances and full period coverage require explicit review.')
        if row.get('managed_intake'):
            from .bank_intake import validate_managed_account
            errors.extend('Bank '+code+': '+message for message in validate_managed_account(row,config))
        registered[code] = row
        coa[code] = {'code': code, 'name': name, 'type': 'Asset',
                     'group': 'Cash and cash equivalents', 'cashflow': 'Internal'}
    return coa, registered


def transfer_pairs(rows, registered, start, end, parse_date, money, errors, reviews=None, context_hash=None):
    """Validate user-assigned pair IDs. Return row-index -> partner index.

    Only same-date, equal-value, opposite-sign transfers between distinct SGD
    accounts are supported in this increment. Unmatched rows never become
    income/expense and cannot silently pass reconciliation.
    """
    groups = defaultdict(list)
    for i, row in enumerate(rows, 1):
        tid = str(row.get('transfer_id', '')).strip()
        if tid:
            groups[tid].append((i, row))
        elif str(row.get('account_code', '')).strip() == 'TRANSFER':
            errors.append(f'Bank row {i}: transfer requires a reviewed pair ID.')
    pairs = {}
    for tid, items in groups.items():
        try:
            if len(items) != 2:
                raise ValueError('exactly two source rows required')
            (i, a), (j, b) = items
            ac, bc = (str(r.get('bank_account_code', '')).strip() for r in (a, b))
            if ac == bc or ac not in registered or bc not in registered:
                raise ValueError('two distinct registered accounts required')
            if any(str(r.get('account_code', '')).strip() != 'TRANSFER' for r in (a,b)):
                raise ValueError('both counter-accounts must be TRANSFER')
            if any(not str(r.get('evidence_ref', '')).strip() or not str(r.get('reference', '')).strip() for r in (a,b)):
                raise ValueError('both source references and evidence IDs required')
            da, db = (parse_date(r.get('date', '')) for r in (a,b))
            if da != db or not start <= da <= end:
                raise ValueError('same-date, in-period transfers only; timing differences require review')
            amounts = []
            for r in (a,b):
                deposit, withdrawal = money(r.get('deposit','')), money(r.get('withdrawal',''))
                if deposit < 0 or withdrawal < 0 or (deposit > 0) == (withdrawal > 0):
                    raise ValueError('exactly one positive deposit or withdrawal per row')
                amounts.append(deposit-withdrawal)
            if amounts[0] + amounts[1] != Decimal('0'):
                raise ValueError('amounts must be equal and opposite; record bank fees separately')
            if tid.startswith('RV-'):
                review=(reviews or {}).get(tid,{})
                if not review.get('reviewer') or not review.get('evidence') or review.get('pair_hash')!=pair_hash(a,b) or review.get('context')!=context_hash:
                    raise ValueError('reviewed suggestion is stale or lacks approval evidence')
            pairs[i], pairs[j] = j, i
        except (ValueError, TypeError) as exc:
            errors.append(f'Transfer {tid}: {exc}.')
    return pairs


def row_facts(row):
    """Persistent source identity, stable across CSV restore and classification changes."""
    keys=('date','bank_account_code','reference','deposit','withdrawal','description','evidence_ref','source_sha256','source_row','source_reference')
    return {k:str(row.get(k) or '').strip() for k in keys}


def fingerprint(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def pair_hash(a,b):
    return fingerprint(sorted([dict(row_facts(r),account_code=str(r.get('account_code') or ''),transfer_id=str(r.get('transfer_id') or '')) for r in (a,b)],key=lambda r:(r['bank_account_code'],r['reference'])))


def transfer_journal_id(tid):
    return 'XFER-'+sha256(tid.encode()).hexdigest()[:16].upper()


def bank_journal_id(code,reference):
    return 'BANK-'+fingerprint([code,reference])[:16].upper()
