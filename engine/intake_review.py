"""Explain possible duplicate or irrelevant uploads for a human to review."""
from collections import defaultdict
from datetime import date
from hashlib import sha256


def upload_id(item):
    """Distinguish renamed copies while keeping retries of the same file stable."""
    return sha256((item['name'] + '\0' + item['sha256']).encode()).hexdigest()


def merge_uploads(existing, incoming):
    files = {upload_id(item): item for item in existing}
    for item in incoming:
        files.setdefault(upload_id(item), item)
    return list(files.values())


def _period(start, end):
    try:
        low, high = date.fromisoformat(start), date.fromisoformat(end)
        return (low, high) if low <= high else None
    except (ValueError, TypeError):
        return None


def flag_uploads(files, parsed, config):
    """Return review reasons, never a deletion or an accounting mutation.

    Content identity proves exact duplicates. Period overlap only signals a
    possible duplicate. Unrecognised files may still be valid supporting evidence.
    """
    documents = {(doc.name, doc.sha256): (doc, acra, bank) for doc, acra, bank in parsed}
    copies = defaultdict(list)
    for item in files:
        copies[item['sha256']].append(item)
    year = _period(config.get('fy_start'), config.get('fy_end')) if config.get('fy_confirmed') else None
    result = []
    for item in files:
        reasons = []
        peers = [f['name'] for f in copies[item['sha256']] if upload_id(f) != upload_id(item)]
        if peers:
            reasons.append('Exact duplicate content of: ' + ', '.join(peers))
        data = documents.get((item['name'], item['sha256']))
        if data is None:
            reasons.append('Could not read this file; relevance needs manual review.')
        else:
            doc, acra, bank = data
            if acra.get('detected') and acra.get('fields'):
                expected = str(config.get('uen', '')).strip().upper()
                actual = str(acra['fields'].get('uen', '')).strip().upper()
                if expected and actual and expected != actual:
                    reasons.append('Company UEN differs from the current workspace; may belong to another company.')
            elif not bank.get('detected'):
                reasons.append('Relevance unclear: not recognised as an ACRA profile or bank statement. May be valid supporting evidence; review before deleting.')
            if bank.get('detected'):
                period = _period(bank.get('period_start'), bank.get('period_end'))
                if year and period:
                    if period[1] < year[0] or period[0] > year[1]:
                        reasons.append('Statement is outside the confirmed financial year; may be needed as opening or comparative evidence.')
                    elif period[0] < year[0] or period[1] > year[1]:
                        reasons.append('Statement includes dates outside the confirmed financial year; review the relevant portion.')
                overlaps = []
                for other, _, other_bank in parsed:
                    if other.sha256 == doc.sha256 or not bank.get('account_id') or bank.get('account_id') != other_bank.get('account_id'):
                        continue
                    other_period = _period(other_bank.get('period_start'), other_bank.get('period_end'))
                    if period and other_period and period[0] <= other_period[1] and other_period[0] <= period[1]:
                        overlaps.append(other.name)
                if overlaps:
                    reasons.append('Possible duplicate coverage: overlaps ' + ', '.join(sorted(set(overlaps))) + '. Contents may differ; review both.')
        if reasons:
            result.append(dict(file_id=upload_id(item), name=item['name'], reasons=reasons))
    return result
