"""Shared Auto exception and current-source readiness controls for multi-bank books."""
from .bank_intake import context,validate_managed_account
from .attention import build_attention,_item
from .clarifications import build_questions,outstanding
from .issue_tracker import sync_issues
from .core import generate


def source_readiness(config,analysis):
    accounts=config.get('bank_accounts',[])
    if not accounts or not analysis or analysis['context']!=context(config):return False
    groups={g['key']:g for g in analysis['groups']}
    if set(groups)!={m.get('account_key') for m in accounts}:return False
    for meta in accounts:
        group=groups.get(meta.get('account_key'))
        if not meta.get('managed_intake') or not group or group['errors'] or validate_managed_account(meta,config):return False
        if [r['summary'] for r in group['sources']]!=meta.get('statements'):return False
    return True


def issues(pkg,analysis,bank_analysis):
    questions=outstanding(build_questions(pkg,analysis['parsed']),pkg.config.get('clarification_answers',{}))
    handled=('uncategorised-','company-details-','financial-year-','fye-not-shown-','no-bank-','confirm-balances-','multiple-bank-accounts-','statement-coverage-','statement-mismatch-','transaction-extraction-')
    questions=[q for q in questions if not q['id'].startswith(handled)]
    items=[i for i in build_attention(pkg,questions,generate(pkg)) if i['id']!='bank-balances']
    mapped={m.get('account_key') for m in pkg.config.get('bank_accounts',[])}
    for group in bank_analysis['groups']:
        details=list(group['errors'])
        if group['key'] not in mapped:details.append('This source account has not been assigned and approved.')
        if details:
            items.append(_item('auto-multi-source-'+group['key'],'Review '+group['bank']+' '+group['masked_account'],
                'Every source account requires independent identity and exact reporting coverage.',
                'Review the account group, originals and missing periods above.',severity='Required',details=details,source_required=True))
    bank_hashes={row['sha256'] for row in analysis['inventory'] if row.get('type')=='Bank statement'}
    unresolved=[row['name']+': '+'; '.join(row['errors']) for row in bank_analysis['inventory']
                if row['sha256'] in bank_hashes and row['errors'] and not row.get('account_key')]
    if unresolved:items.append(_item('auto-multi-unidentified','Identify unresolved bank originals','Some bank sources cannot be grouped safely.',
        'Supply readable originals with full account identity, or resolve obsolete sources explicitly.',severity='Required',details=unresolved,source_required=True))
    if not source_readiness(pkg.config,bank_analysis):
        items.append(_item('auto-multi-recheck','Recheck current bank sources','Current originals do not establish approved coverage for every registered account.',
            'Re-upload originals and review each account. Saved ZIPs retain metadata, not original PDFs.',severity='Required',source_required=True))
    return sync_issues(pkg.config,items,sources_available=source_readiness(pkg.config,bank_analysis)),questions
