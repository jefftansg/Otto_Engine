"""Derive tab readiness from existing review gates; colours never approve entries."""
from .clarifications import build_questions, outstanding
from .core import generate
from .intake_review import flag_uploads


def stage_statuses(pkg, parsed, batch, files=(), decisions=None):
    cfg = pkg.config
    questions = outstanding(build_questions(pkg, parsed, batch), cfg.get('clarification_answers', {}))
    result = generate(pkg)
    pending_sections = {q['section'] for q in questions}
    decisions = decisions or {}
    flags = flag_uploads(files, parsed, cfg)
    uploads_ok = bool(files) and len(parsed)==len(files) and all(decisions.get(f['file_id'])==f['reasons'] for f in flags)
    company_ok = bool(cfg.get('company_name') and cfg.get('uen') and cfg.get('fy_confirmed')) and 'Company' not in pending_sections
    bank_started = bool(pkg.bank or batch.get('detected_banks') or cfg.get('bank_balances_confirmed'))
    uncoded = any(str(r.get('account_code') or '9999').strip() in ('','9999') for r in pkg.bank)
    source_recheck = any(r.get('source_required') and r.get('status')=='Needs recheck' for r in cfg.get('issue_register', {}).values())
    bank_errors = any(any(word in e.lower() for word in ('bank','cash flow')) for e in result['errors'])
    bank_ok = bool(pkg.bank) and cfg.get('bank_balances_confirmed') and not uncoded and not bank_errors and not source_recheck and not pending_sections.intersection({'Bank','Transactions'})
    other_started = bool(cfg.get('simple_questions') or cfg.get('clarification_answers') or pkg.claims or pkg.journals or pkg.invoices)
    other_ok = bool(cfg.get('other_records_confirmed')) and not pending_sections.intersection({'Accounting','Other records'})
    reports_started = bool(cfg.get('company_name') or bank_started or other_started)
    reports_ok = bool(company_ok and bank_ok and other_ok and not questions and not result['errors'])
    started = [bool(files), bool(cfg.get('company_name') or cfg.get('uen') or cfg.get('fy_confirmed')), bank_started, other_started, reports_started]
    cleared = [uploads_ok, company_ok, bank_ok, other_ok, reports_ok]
    return ['Cleared' if ok else 'Needs attention' if began else 'Not started' for ok,began in zip(cleared,started)]


def tab_labels(stages, statuses):
    styles = {'Cleared':('green','✓'), 'Needs attention':('orange','!'), 'Not started':('gray','○')}
    return [f":{styles[status][0]}[{styles[status][1]} {label} · {status}]" for label,status in zip(stages,statuses)]
