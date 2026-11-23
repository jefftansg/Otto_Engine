"""Direct plain-language replies are facts for review, never automatic ledger postings."""
from copy import deepcopy
from datetime import datetime,timezone
import re
from .auto import digest
from .clarification_workbook import _items,_current,_text,_reply,context,source_revision,TYPES

MANUAL='Other / type manually'
WAITING='Needs reply'
TX_CHOICES=[WAITING]+[v for v in TYPES if v!='Other']+[MANUAL]
QUESTION_CHOICES=[WAITING,'Yes','No','Not sure','Not applicable',MANUAL]


def query_state(pkg,questions):
    items=_items(pkg,questions)
    revision=digest(dict(context=context(pkg),sources=source_revision(pkg),items=items,answers={k:_current(pkg,k) for k in items}))
    return dict(items=items,revision=revision)


def reply_record(pkg,key):
    return pkg.config.get('transaction_clarifications' if key.startswith('T-') else 'clarification_answers',{}).get(key,{})


def save_direct_replies(pkg,questions,revision,rows,reviewer):
    state=query_state(pkg,questions)
    if revision!=state['revision']:raise ValueError('The questions or source details changed. Refresh before saving replies.')
    if not reviewer.strip():raise ValueError('Enter the name of the person recording these replies.')
    seen=set();answers=[]
    for row in rows:
        key=row.get('id');item=state['items'].get(key)
        if not item or key in seen:raise ValueError('A query is missing or repeated. Refresh the reply list.')
        seen.add(key);transaction=item['sheet']=='Transactions'
        choice=_text(row.get('choice'));manual=_text(row.get('manual'));explanation=_text(row.get('answer'))
        if choice in ('',WAITING) and not manual and not explanation:continue
        if choice in ('',WAITING):choice=MANUAL
        if choice not in (TX_CHOICES if transaction else QUESTION_CHOICES):raise ValueError('Choose a listed reply option or Other / type manually.')
        if choice==MANUAL and not (manual or explanation):continue  # Unanswered questions remain open.
        if not transaction and choice in ('Yes','No') and not re.match(r'^(?:Did|Was|Were|Has|Have|Is|Are|Can|Does|Do)\b',item['fixed'][1],re.I):
            raise ValueError('This question needs a name or explanation: '+item['fixed'][1]+' Choose Other / type manually.')
        if choice==MANUAL:answer=(manual+': '+explanation if manual and explanation else manual or explanation)
        else:answer=(explanation or choice) if transaction else choice+(': '+explanation if explanation else '')
        selected_status=_text(row.get('status')) or 'Answered'
        if selected_status not in ('Answered','Need more information','Not applicable'):raise ValueError('Choose a listed reply status.')
        status='Needs answer' if choice=='Not sure' or selected_status=='Need more information' else 'Not applicable' if choice=='Not applicable' or selected_status=='Not applicable' else 'Answered'
        if answer.casefold() in ('not sure','unknown','do not know',"don't know"):status='Needs answer'
        incoming=dict(answer=answer,money_type=('Other' if choice==MANUAL else choice) if transaction else '',
                      document=_text(row.get('document')),answered_by=_text(row.get('answered_by')),status=status)
        if any(len(v)>5000 for v in incoming.values()):raise ValueError('Keep each reply field within 5,000 characters; use document references for longer details.')
        if incoming==_current(pkg,key):continue
        answers.append(dict(id=key,kind='Transaction' if transaction else 'Question',row=item.get('index'),
                            reply_choice=choice,manual_reply=manual,explanation=explanation,**incoming))
    if not answers:return 0
    cfg=deepcopy(pkg.config);at=datetime.now(timezone.utc).isoformat(timespec='seconds');previous={}
    for reply in answers:
        store='transaction_clarifications' if reply['kind']=='Transaction' else 'clarification_answers'
        target=cfg.setdefault(store,{});previous[reply['id']]=deepcopy(target.get(reply['id']))
        target[reply['id']]=dict(reply,reviewer=reviewer.strip(),reviewed_at=at,source='Entered in Otto',export_id=None)
    cfg.setdefault('clarification_import_history',[]).append(dict(export_id=None,source='Entered in Otto',context=context(pkg),
        reviewer=reviewer.strip(),at=at,count=len(answers),previous=previous,answers=deepcopy(answers)))
    pkg.config=cfg
    return len(answers)


def suggested_category(reply):
    """Only clear expense/sale labels map to existing category proposals; no posting."""
    if reply.get('status')!='Answered':return None
    return {'Sale':'4000','Bank charges':'5100','Office / rent':'5200','Marketing':'5300',
            'Software subscriptions':'5400','Professional fees':'5500'}.get(reply.get('money_type'))
