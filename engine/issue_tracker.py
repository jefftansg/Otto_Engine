"""Persist issue progress while live checks, rather than a checkbox, clear issues."""
from copy import deepcopy
from datetime import datetime, timezone
from .core import csv_bytes


def sync_issues(config, items, *, sources_available=True, now=None):
    stamp = now or datetime.now(timezone.utc).isoformat(timespec='seconds')
    register = config.setdefault('issue_register', {})
    current = {item['id']: item for item in items}
    for key, item in current.items():
        record = register.setdefault(key, dict(first_seen=stamp, notes='', events=[]))
        previous = record.get('status')
        record.update(deepcopy(item))
        record['last_seen'] = stamp
        record['status'] = 'In progress' if previous == 'In progress' else 'Open'
        if record['status'] != previous:
            record['events'].append(dict(at=stamp, status=record['status']))
        record.pop('cleared_at', None)
    answers = config.get('clarification_answers', {})
    for key, record in register.items():
        if key in current:
            continue
        answered = answers.get(record.get('question_id'), {}).get('status') in ('Answered', 'Not applicable')
        status = 'Needs recheck' if record.get('source_required') and not sources_available and not answered else 'Cleared'
        if record.get('status') != status:
            record['status'] = status
            record['events'].append(dict(at=stamp, status=status))
            if status == 'Cleared':
                record['cleared_at'] = stamp
            else:
                record.pop('cleared_at', None)
    return sorted(register.values(), key=lambda r: (r['status']=='Cleared', r['severity']!='Required', r['id']))


def update_issue(config, key, status, note, *, now=None):
    """User progress notes cannot bypass checks or close a live accounting issue."""
    record = config.get('issue_register', {}).get(key)
    if record is None or record['status'] == 'Cleared' or status not in ('Open', 'In progress'):
        return False
    stamp = now or datetime.now(timezone.utc).isoformat(timespec='seconds')
    updated = dict(at=stamp, status=status, note=note.strip())
    if record['status'] != status or record.get('notes', '') != note.strip():
        record['events'].append(updated)
    # Missing source evidence must remain explicitly unverified.
    if record['status'] != 'Needs recheck':
        record['status'] = status
    record['notes'] = note.strip()
    return True


def issues_csv(records):
    rows = [dict(id=r['id'], priority=r['severity'], issue=r['title'], status=r['status'],
                 reason=r['why'], details=' | '.join(r.get('details', [])), action=r['question'],
                 notes=r.get('notes',''), first_seen=r['first_seen'], cleared_at=r.get('cleared_at',''))
            for r in records]
    return csv_bytes(rows, ['id','priority','issue','status','reason','details','action','notes','first_seen','cleared_at'])
