"""Read-only preparation progress; completion is never professional approval."""
from datetime import date
from .core import generate
from .auto_multi import source_readiness


def workflow_progress(pkg,files,analysis=None,banks=None,result=None,bundle_current=False):
    cfg=pkg.config
    try:
        low,high=date.fromisoformat(cfg.get('fy_start','')),date.fromisoformat(cfg.get('fy_end',''))
        setup=bool(cfg.get('company_name') and cfg.get('uen') and cfg.get('fy_confirmed') and low<=high and (high-low).days<=732)
    except (ValueError,TypeError):setup=False
    uploaded=bool(files)
    multi='bank_accounts' in cfg
    if multi:
        bank_ok=setup and source_readiness(cfg,banks)
    else:
        accounts=(analysis or {}).get('accounts',[])
        bank_ok=bool(setup and uploaded and cfg.get('bank_balances_confirmed') and accounts and
                     all(a['coverage']['balances']['ready'] for a in accounts))
    result=result if result is not None else generate(pkg)
    reconciled=bool(bank_ok and not result['errors'])
    generated=bool(reconciled and bundle_current)
    stages=[dict(id='documents',label='Upload documents',done=uploaded),
            dict(id='company',label='Confirm company',done=setup),
            dict(id='accounts',label='Review bank accounts',done=bool(bank_ok)),
            dict(id='records',label='Reconcile records',done=reconciled),
            dict(id='reports',label='Generate draft reports',done=generated)]
    current=next((s for s in stages if not s['done']),None)
    actions={'documents':'Add originals using the drop box below.',
             'company':'Review company details and click Confirm setup.',
             'accounts':'Approve each account’s identity, full-period coverage and balances.',
             'records':'Review categories, transfers and opening journals; clear blocking errors.',
             'reports':'Resolve remaining review items and generate the provisional package.'}
    for stage in stages:stage['status']='Done' if stage['done'] else 'Current' if stage is current else 'Pending'
    return dict(stages=stages,completed=sum(s['done'] for s in stages),total=len(stages),
                current=current['label'] if current else 'Draft package generated',
                next=actions[current['id']] if current else 'Review the draft package. Professional/template authorisation remains separate.')
