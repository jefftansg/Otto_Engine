"""Explainable next actions for the Guided Mode accounting triage.

Each item points either to a guided step or a specific Advanced workspace.
No changes to journals or bank records are made by this module. Clarification
answers are not treated as proof that an accounting entry has been corrected.
"""
from __future__ import annotations
from collections import defaultdict

SECTIONS = {
    'Company': (1, 0), 'Bank': (2, 0), 'Transactions': (2, 2),
    'Accounting': (3, 4), 'Other records': (3, 3),
}
ADVANCED_PAGES = [
    'Setup & documents', 'Dashboard', 'Bank transactions', 'Director claims',
    'Manual journals', 'Receivables', 'Evidence register', 'Reports & checks',
]


def _item(key, title, explanation, question, *, severity='Needs attention', stage=3,
          advanced_page=7, affected=0):
    return {'id': key, 'title': title, 'why': explanation, 'question': question,
            'severity': severity, 'guided_stage': stage,
            'advanced_page': advanced_page, 'affected': affected}


def _route_error(message):
    """Give validation errors a sensible place to edit, without losing them."""
    s = message.lower()
    if 'claim' in s or 'director ' in s:
        return 'Director claims', 3
    if 'invoice' in s or 'receivable' in s or 'ar ' in s:
        return 'Receivables', 5
    if 'journal' in s or 'manual row' in s:
        return 'Manual journals', 4
    if 'bank' in s or 'cash flow' in s:
        return 'Bank reconciliation', 0
    if 'financial year' in s or 'company name' in s or 'framework' in s:
        return 'Company details', 0
    return 'Financial report checks', 7


def build_attention(pkg, questions=(), result=None, bank_batch=None):
    """Prioritised, actionable issues from live data. Nothing is auto-posted.

    The returned dicts are presentation-independent and can be used by other
    interfaces or a future client-facing intake portal.
    """
    cfg = pkg.config
    items = []
    if not (cfg.get('company_name') and cfg.get('uen') and cfg.get('fy_confirmed')):
        items.append(_item('company-setup','Confirm the company and financial year',
              'The reports need an exact registered name, UEN and financial year that you have checked.',
              'Can you confirm the registered company details and the financial year-end?',
              severity='Required',stage=1,advanced_page=0))

    bank_present = bool(pkg.bank or (bank_batch and bank_batch.get('detected_banks')))
    if bank_present and not cfg.get('bank_balances_confirmed'):
        items.append(_item('bank-balances','Check the bank opening and closing balances',
             'The statement balances have not been confirmed against the reporting period.',
             'Do the opening and year-end bank balances match the original statements?',
             severity='Required',stage=2,advanced_page=0))

    if bank_batch and bank_batch.get('detected_banks'):
        problems = list(bank_batch.get('issues') or [])+list(bank_batch.get('mismatches') or [])
        problems += list((bank_batch.get('balances') or {}).get('errors') or [])
        if bank_batch.get('outside'):
            problems.append(f"{len(bank_batch['outside'])} transaction(s) are outside the year")
        if problems:
            items.append(_item('bank-source-issues','Check incomplete or inconsistent bank statements',
                'Some statement periods, transactions or totals need checking. No unverified rows should be posted.',
                'Can you provide the missing statements or a bank-exported CSV/Excel file?',
                severity='Required',stage=2,advanced_page=0,affected=len(problems)))

    uncoded=[r for r in pkg.bank if str(r.get('account_code','') or '9999').strip() in ('','9999')]
    if uncoded:
        items.append(_item('bank-uncoded',f'{len(uncoded)} bank transaction(s) need a category',
           'The engine cannot determine whether these transactions are sales, transfers, loans or expenses.',
           'What was each payment or receipt for? Check an invoice, receipt or the person who made the transfer.',
           severity='Required',stage=2,advanced_page=2,affected=len(uncoded)))

    responses=cfg.get('simple_questions',{})
    if responses.get('director_expenses')=='Yes' and not pkg.claims:
        items.append(_item('director-records','Record expenses paid personally by directors',
           'You indicated directors paid company bills, but no expense claims are entered.',
           'Who paid, what was bought, and are these amounts repayable or capital contributions?',
           severity='Required',stage=3,advanced_page=3))
    if responses.get('receivables')=='Yes' and not pkg.invoices:
        items.append(_item('unpaid-customer-invoices','Check customer invoices still unpaid',
           'You indicated customers owe money, but no receivables schedule is entered.',
           'Which invoices were unpaid at the financial year-end and what were the amounts?',
           severity='Required',stage=3,advanced_page=5))

    if result:
        groups=defaultdict(list)
        for error in result.get('errors',[]):
            label,page=_route_error(str(error))
            groups[(label,page)].append(str(error))
        for (label,page),errors in groups.items():
            # Source transaction classification and basic setup already have an
            # explicit, friendlier callout; the remaining checks must stay visible.
            if label=='Company details' and all('company name and UEN' in e.lower() for e in errors):
                continue
            if label=='Bank reconciliation' and bank_present and not cfg.get('bank_balances_confirmed') and all('opening bank statement' in e.lower() for e in errors):
                continue
            items.append(_item('validation-'+str(page)+'-'+label.lower().replace(' ','-'),
                f'{len(errors)} {label.lower()} check(s) need correction',
                'The accounting engine flagged: '+'; '.join(errors[:2]) + ('…' if len(errors)>2 else ''),
                'Can you verify the source records and correct the affected entries?',
                severity='Required',stage=2 if page in (0,2) else 3,
                advanced_page=page,affected=len(errors)))

    open_q=[q for q in questions if q.get('priority')=='Required']
    normal_q=[q for q in questions if q.get('priority')!='Required']
    if open_q:
        items.append(_item('required-questions',f'{len(open_q)} important question(s) are unanswered',
            'These questions require information or documentation from the director or client.',
            open_q[0]['question'],severity='Required',stage=3,advanced_page=7,affected=len(open_q)))
    if normal_q:
        items.append(_item('general-questions',f'{len(normal_q)} other question(s) to clarify',
           'Some notes, confirmations or supporting documents are still needed.',
           normal_q[0]['question'],severity='Follow up',stage=3,advanced_page=7,affected=len(normal_q)))

    # Sort by priority, retaining actionable grouping, and stable IDs.
    return sorted(items,key=lambda x:(0 if x['severity']=='Required' else 1,x['id']))


def counts(items):
    return {'total':len(items),'required':sum(x['severity']=='Required' for x in items),
            'follow_up':sum(x['severity']!='Required' for x in items),
            'transactions':sum(x['affected'] for x in items if x['id']=='bank-uncoded')}
