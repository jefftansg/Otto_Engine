"""Freeze a shared-ledger snapshot; export provisional reports with traceable layout IDs."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from .auto import digest
from .core import generate
from .report_layouts import layout
from .reports import management_pdf, financial_statements_pdf, xlsx_report

TEMPLATES = {
    'ma': dict(id='otto-ma-classic-v1', status='Provisional layout - owner approval pending',
               orientation='A4 landscape', margins_mm=dict(left=15,right=15,top=23,bottom=19),
               font='Helvetica', title_pt=17, body_pt=9),
    'ufs': dict(id='otto-ufs-classic-v1', status='Provisional layout - owner approval pending',
                orientation='A4 portrait', margins_mm=dict(left=19,right=19,top=23,bottom=20),
                font='Helvetica', title_pt=17, body_pt=9),
}


def frozen_report(pkg, analysis, issues):
    frozen=deepcopy(pkg)
    result=generate(frozen)
    active=[i for i in issues if i['status']!='Cleared']
    complete=bool(analysis['accounts']) and all(a['coverage']['balances']['ready'] for a in analysis['accounts'])
    inventory=analysis['inventory']
    complete=complete and bool(inventory) and not any(r.get('demo') or r.get('status')=='Excluded company mismatch' for r in inventory)
    ready=bool(complete and frozen.config.get('fy_confirmed') and frozen.config.get('bank_balances_confirmed')
               and frozen.config.get('other_records_confirmed') and not result['errors'] and not active)
    semantic_config={k:v for k,v in frozen.config.items() if k!='issue_register'}
    semantic_issues=[{k:r.get(k) for k in ('id','status','notes','details')} for r in active]
    snapshot=digest(dict(config=semantic_config,exceptions=semantic_issues,bank=frozen.bank,claims=frozen.claims,journals=frozen.journals,
                         invoices=frozen.invoices,evidence=frozen.evidence,inventory=inventory))
    templates=deepcopy(TEMPLATES)
    for kind in templates:
        key,tokens=layout(frozen.config,kind)
        templates[kind].update(id=key,typography=tokens,font_substitution='Helvetica replaces Arial/Liberation Sans; visual approval pending')
    meta=dict(snapshot=snapshot, status='DRAFT - REVIEW REQUIRED' if ready else 'PROVISIONAL - INCOMPLETE RECORDS',
              templates=templates, template_approved=False, authorised=False,
              renderer_sha256=sha256(Path(__file__).with_name('reports.py').read_bytes()).hexdigest(),
              exceptions=deepcopy(active), inventory=deepcopy(inventory))
    meta['report_revision']=digest(dict(snapshot=snapshot,templates=templates,renderer=meta['renderer_sha256']))
    result['auto_report']=meta
    return result,meta


def export_bundle(result, meta):
    outputs={'Management_Accounts_PROVISIONAL.pdf':management_pdf(result),
             'Financial_Workpapers_PROVISIONAL.xlsx':xlsx_report(result),
             'Source_inventory.json':json.dumps(meta['inventory'],indent=2).encode(),
             'Exceptions.json':json.dumps(meta['exceptions'],indent=2).encode()}
    if result['config'].get('entity_type')=='Private limited company':
        outputs['Unaudited_FS_PROVISIONAL.pdf']=financial_statements_pdf(result)
    manifest={k:v for k,v in meta.items() if k not in ('inventory','exceptions')}
    manifest['files']={name:sha256(payload).hexdigest() for name,payload in outputs.items()}
    outputs['Report_manifest.json']=json.dumps(manifest,indent=2).encode()
    buffer=BytesIO()
    with ZipFile(buffer,'w',compression=ZIP_DEFLATED) as archive:
        for name,payload in outputs.items():archive.writestr(name,payload)
    return buffer.getvalue()
