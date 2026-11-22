"""Simple guided onboarding for non-accountants.

No upload is posted without a human confirmation. Cached uploads are held only
in Streamlit's memory; saved workspaces intentionally exclude the source PDFs.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import streamlit as st

from engine.core import COA_MAP, csv_bytes, generate, money_str
from engine.importers import existing_duplicates, empty_company
from engine.reports import management_pdf, financial_statements_pdf, xlsx_report
from engine.autofill import extract_acra_profile, extract_bank_statement, consolidate_statement_balances, suggested_start, propose_bank_rows
from engine.clarifications import OTHER_RECORDS, build_questions, outstanding, questions_csv, questions_pdf
from engine.attention import build_attention, counts, ADVANCED_PAGES
from engine.intake_review import upload_id, merge_uploads, flag_uploads
from engine.issue_tracker import sync_issues, update_issue, issues_csv
from engine.stages import stage_statuses, tab_labels
from engine.document_history import statement_history_controls

STAGES = ['1  Company', '2  Documents', '3  Bank', '4  Other records', '5  Reports']


def _go(i: int):
    st.session_state['guided_stage'] = max(0, min(len(STAGES)-1, i))
    st.session_state['guided_navigation_revision'] = st.session_state.get('guided_navigation_revision',0)+1


def _date(raw, default):
    try: return date.fromisoformat(str(raw))
    except (ValueError, TypeError): return default


def _load_documents(inspect):
    parsed = []
    for item in st.session_state.get('guided_files', []):
        try:
            doc = inspect(item['name'], item['bytes'])
            acra = extract_acra_profile(doc) if item['name'].lower().endswith('.pdf') else {'detected':False,'fields':{}}
            bank = extract_bank_statement(doc)
            parsed.append((doc, acra, bank))
        except Exception as e:
            st.error(f"Could not read **{item['name']}**: {e}")
    return parsed


def _delete_uploads(pkg, file_ids, bank_hashes=()):
    """Remove session uploads without deleting approved accounting/evidence records."""
    files = st.session_state.get('guided_files', [])
    selected = set(file_ids)
    if not selected or not selected.issubset({upload_id(f) for f in files}):
        return False
    removed = [f for f in files if upload_id(f) in selected]
    removed_hashes = {f['sha256'] for f in removed}
    register = pkg.config.get('statement_register', [])
    removed_names = {f['name'] for f in removed}
    linked = any(s.get('sha256') in removed_hashes or
                 (not s.get('sha256') and s.get('source') in removed_names)
                 for s in register)
    if removed_hashes.intersection(bank_hashes) or linked:
        pkg.config['bank_balances_confirmed'] = False
        pkg.config['bank_balance_source'] = 'Uploaded bank statement deleted: reconfirm bank balances'
    # Saved evidence and statement registers retain their historical provenance.
    st.session_state['guided_files'] = [f for f in files if upload_id(f) not in selected]
    decisions = st.session_state.get('guided_file_decisions', {})
    st.session_state['guided_file_decisions'] = {k: v for k, v in decisions.items() if k not in selected}
    # Remount the uploader so its old selection cannot silently restore a deleted file.
    st.session_state['guided_upload_version'] = st.session_state.get('guided_upload_version', 0) + 1
    st.session_state.pop('guided_import_checked', None)
    st.session_state['guided_deleted_notice'] = f'{len(removed)} uploaded file(s) deleted. Saved transactions and evidence were retained.'
    return True


def _upload_deletion_controls(pkg, parsed, inspect, scope):
    bank_hashes = {doc.sha256 for doc, acra, bank in parsed if bank.get('detected')}
    files = st.session_state.get('guided_files', [])
    if not files:
        return
    names = {upload_id(f): f['name'] for f in files}
    flagged = [f for f in flag_uploads(st.session_state.get('guided_files', []), parsed, pkg.config)
               if f['file_id'] in names]
    decisions = st.session_state.setdefault('guided_file_decisions', {})
    if flagged:
        st.markdown('**Flagged files — your decision**')
        st.caption('Flags are suggestions for review. No file is deleted automatically. Retained files stay visible, and accounting import checks still apply.')
        st.dataframe([{'File': f['name'], 'Flag': ' | '.join(f['reasons']),
                       'Decision': 'Retained' if decisions.get(f['file_id']) == f['reasons'] else 'Awaiting your decision'}
                      for f in flagged], hide_index=True, width='stretch')
    with st.expander('Review or delete uploaded files', expanded=bool(flagged)):
        st.caption('Remove files from this session and refresh extracted summaries. Saved transactions, company details and evidence remain. Bank balances must be rechecked after deleting a statement. Original files on your computer are kept.')
        selected = st.multiselect('Select files to retain or delete', list(names),
                                 format_func=lambda h: names[h] + ' · ' + h[:8],
                                 key='guided_delete_'+scope+'_'+str(st.session_state.get('guided_upload_version', 0)))
        if st.button('Retain selected files', key='guided_retain_button_'+scope, disabled=not selected, on_click=_go, args=(1 if scope=='upload' else 2,)):
            for f in flagged:
                if f['file_id'] in selected:
                    decisions[f['file_id']] = f['reasons']
            st.rerun()
        if st.button('Delete selected files', key='guided_delete_button_'+scope, disabled=not selected, on_click=_go, args=(1 if scope=='upload' else 2,)):
            if _delete_uploads(pkg, selected, bank_hashes):
                if hasattr(inspect, 'clear'):
                    inspect.clear()
                st.rerun()


def _money_sum(rows, field):
    return sum((Decimal(str(r.get(field,'') or '0')) for r in rows), Decimal('0'))


def _bank_batch(parsed, cfg, existing):
    rows=[]; issues=[]; mismatches=[]
    detected_banks=[]
    seen=set()
    for doc, acra, bank in parsed:
        if bank.get('detected'):
            if doc.sha256 in seen:continue
            seen.add(doc.sha256)
            detected_banks.append(bank)
            proposed, warnings = propose_bank_rows(doc)
            rows.extend(proposed)
            issues.extend(f'{doc.name}: {s}' for s in warnings)
            if proposed and bank.get('opening') is not None and bank.get('closing') is not None:
                change = _money_sum(proposed,'deposit') - _money_sum(proposed,'withdrawal')
                expected = Decimal(bank['closing']) - Decimal(bank['opening'])
                if change != expected:
                    mismatches.append(f'{doc.name}: extracted transactions change the balance by S${change:,.2f}, but the statement says S${expected:,.2f}.')
    duplicates = existing_duplicates(existing,rows,'bank') if rows else []
    # Uploaded statements stay in session after import. Do not claim that an
    # already-completed import is a new problem or offer to post it again.
    already_imported=bool(rows) and len(duplicates)==len(rows)
    outside=[]
    try:
        low = date.fromisoformat(cfg.get('fy_start',''))
        high = date.fromisoformat(cfg.get('fy_end',''))
        outside=[r for r in rows if not low<=date.fromisoformat(r['date'])<=high]
    except (ValueError,TypeError):
        outside=rows
    proposal = consolidate_statement_balances(detected_banks,cfg.get('fy_start'),cfg.get('fy_end'))
    return dict(rows=rows,issues=issues,mismatches=mismatches,duplicates=duplicates,outside=outside,balances=proposal,detected_banks=detected_banks,already_imported=already_imported)


def _status(label, done, todo):
    if done:
        st.success(f'✓ {label}')
    else:
        st.warning(f'Needs attention: **{label}** — {todo}')



def _advanced(page: int):
    """A user-initiated switch to a particular detailed accounting editor."""
    st.session_state['app_mode']='Advanced'
    st.session_state['advanced_page']=page


def _open_issue(issue):
    if issue.get('question_id'):
        st.session_state['question_focus_id'] = issue['question_id']
    _go(1 if issue['status'] == 'Needs recheck' else issue['guided_stage'])


def _issue_records(pkg, parsed, batch):
    questions = outstanding(build_questions(pkg, parsed, batch), pkg.config.get('clarification_answers', {}))
    items = build_attention(pkg, questions, generate(pkg), batch)
    return sync_issues(pkg.config, items, sources_available=bool(batch.get('detected_banks')))


def _attention_panel(pkg, records, scope):
    """List every active issue, track work, and preserve cleared history."""
    active = [r for r in records if r['status'] != 'Cleared']
    cleared = [r for r in records if r['status'] == 'Cleared']
    st.markdown('### What needs your attention?')
    summary = counts(active)
    if active:
        st.info(f"{summary['required']} important issue(s) and {summary['follow_up']} follow-up item(s) remain. Select an issue below to handle it.")
        st.dataframe([{'Issue':r['title'], 'Priority':r['severity'], 'Status':r['status'],
                       'Next action':'Upload source documents to recheck' if r['status']=='Needs recheck' else r['question']}
                      for r in active], hide_index=True, width='stretch')
        ids = [r['id'] for r in active]
        chosen = st.selectbox('Issue to handle', ids,
                              format_func=lambda key: next(r['title']+' · '+r['status']+' · '+r['id'] for r in active if r['id']==key),
                              key='issue_picker_'+scope)
        issue = next(r for r in active if r['id']==chosen)
        st.write('**Why it was raised:** '+issue['why'])
        if issue['status'] == 'Needs recheck':
            st.warning('The source files are no longer available in this session. This issue remains open until the documents are uploaded and the checks can run again.')
        for detail in issue.get('details', []):
            st.write('• '+str(detail))
        st.write('**What to do:** '+issue['question'])
        c1,c2,c3 = st.columns(3)
        with c1:
            action = 'Upload documents to recheck' if issue['status']=='Needs recheck' else 'Answer this question' if issue.get('question_id') else 'Go to '+STAGES[issue['guided_stage']].strip()
            st.button(action, key='issue_fix_'+scope, on_click=_open_issue, args=(issue,), width='stretch', type='primary')
        with c2:
            st.button('Advanced review', key='issue_advanced_'+scope, on_click=_advanced,
                      args=(issue['advanced_page'],), help='Opens '+ADVANCED_PAGES[issue['advanced_page']], width='stretch')
        with c3:
            if st.button('Recheck issues', key='issue_recheck_'+scope, width='stretch', on_click=_go, args=(int(scope),)):
                st.rerun()
        with st.form('issue_progress_'+scope+'_'+issue['id']):
            status = st.radio('Work status', ['Open','In progress'],
                              index=1 if issue['status']=='In progress' else 0, horizontal=True)
            note = st.text_area('Progress / action taken', value=issue.get('notes',''))
            if st.form_submit_button('Save issue progress', on_click=_go, args=(int(scope),)):
                update_issue(pkg.config, issue['id'], status, note)
                st.rerun()
    else:
        st.success('All tracked issues are cleared by the current checks. A final professional review is still required.')
    st.caption('The list is rechecked as records change. Progress notes do not clear an issue or approve an accounting entry. Cleared items remain in history. Save your workspace ZIP to keep issue history and notes.')
    if cleared:
        with st.expander(f'Cleared issues ({len(cleared)})'):
            st.dataframe([{'Issue':r['title'], 'Status':r['status'], 'Cleared at (UTC)':r.get('cleared_at',''),
                           'Progress / action taken':r.get('notes','')} for r in cleared], hide_index=True, width='stretch')
    if records:
        st.download_button('Download issue list (CSV)', issues_csv(records),
                           file_name='Otto_Issue_Tracker.csv', mime='text/csv', key='issue_csv_'+scope)
    st.divider()


def _question_panel(pkg, parsed, batch):
    """A client-ready clarification list with actionable answers and downloads."""
    cfg=pkg.config
    questions=build_questions(pkg, parsed, batch)
    answers=cfg.get('clarification_answers',{})
    open_items=outstanding(questions,answers)
    required=[q for q in open_items if q['priority']=='Required']
    st.markdown('### Your questions to clarify')
    st.caption('Created automatically from the documents, missing records and unanswered questions. You can send this list to your client, or complete it yourself. It updates as information is supplied.')
    a,b,c=st.columns(3)
    a.metric('Questions generated',len(questions))
    b.metric('Still need answers',len(open_items))
    c.metric('Important open questions',len(required))
    if not questions:
        st.success('No questions were identified from the current records. A professional review of disclosures is still necessary.')
    else:
        st.caption('Choose one question below, record the answer, then save. The question will disappear from the outstanding list, but financial entries will NOT change automatically.')
        if open_items:
            choices=list(range(len(open_items)))
            current_id=st.session_state.get('question_focus_id','')
            current_idx=next((i for i,q in enumerate(open_items) if q['id']==current_id),0)
            selected_idx=st.selectbox('Question to resolve',choices,index=current_idx,
                format_func=lambda i: ('Important: ' if open_items[i]['priority']=='Required' else '') +open_items[i]['question'],
                key='question_picker_'+hashlib.sha256('|'.join(q['id'] for q in open_items).encode()).hexdigest()[:10])
            q=open_items[selected_idx]
            st.info(q['why'])
            st.caption('What to request: '+q['request'])
            with st.form('single_question_answer'):
                previous=answers.get(q['id'],{})
                status=st.radio('What is the outcome?', ['Answered','Not applicable','Still waiting'],
                    index=0 if previous.get('status')=='Answered' else 1 if previous.get('status')=='Not applicable' else 2,
                    horizontal=True)
                reply=st.text_area('Answer / supporting record / reason',
                    value=previous.get('answer',''),placeholder='e.g. Director confirms these were loan repayments; supporting bank advice attached.')
                if st.form_submit_button('Save this answer',on_click=_go,args=(3,),type='primary'):
                    if status!='Still waiting' and not reply.strip():
                        st.error('Write the answer or reason before closing a question.')
                    else:
                        updated=dict(answers)
                        updated[q['id']]={'status':('Needs answer' if status=='Still waiting' else status),'answer':reply.strip()}
                        cfg['clarification_answers']=updated
                        st.session_state['question_focus_id']=''
                        st.rerun()
        else:
            st.success('All generated questions currently have recorded answers or reasons. Verify evidence and journal adjustments before issuing reports.')
        with st.expander('Optional: edit multiple answers in a table'):
            rows=[]
            for q in questions:
                prev=answers.get(q['id'],{})
                rows.append({'Priority':q['priority'],'Topic':q['section'],'Question':q['question'],
                            'Status':prev.get('status','Needs answer'), 'Answer or note':prev.get('answer','')})
            edited=st.data_editor(rows,num_rows='fixed',hide_index=True,width='stretch',
                   disabled=['Priority','Topic','Question'],
                   column_config={'Status':st.column_config.SelectboxColumn('Status',options=['Needs answer','Answered','Not applicable'],required=True),
                       'Answer or note':st.column_config.TextColumn('Answer or note',width='large')},
                   key='clarification_grid_'+__import__('hashlib').sha256('|'.join(q['id'] for q in questions).encode()).hexdigest()[:14])
            if st.button('Save all edited answers',on_click=_go,args=(3,),type='primary',key='save_clarifications',width='stretch'):
                updated=dict(answers);bad=[]
                for q,r in zip(questions,edited):
                    state=r.get('Status','Needs answer');note=str(r.get('Answer or note') or '').strip()
                    if state in ('Answered','Not applicable') and not note:
                        bad.append(q['question']);continue
                    updated[q['id']]={'status':state,'answer':note}
                if bad:
                    st.error(f'{len(bad)} answered/not-applicable question(s) are missing an explanation.')
                else:
                    cfg['clarification_answers']=updated
                    st.rerun()
        with st.expander('See why each question was asked and what to request'):
            for q in questions:
                if q in open_items:
                    st.markdown(f"**{q['section']} — {q['question']}**")
                    st.caption(q['why']+'  |  Ask for: '+q['request'])
        col_pdf,col_csv=st.columns(2)
        with col_pdf:
            st.download_button('Download client questions (PDF)',questions_pdf(cfg.get('company_name'),questions,answers),
                               file_name='Client_Questions_To_Clarify.pdf',mime='application/pdf',width='stretch')
        with col_csv:
            st.download_button('Download questions and answers (CSV)',questions_csv(questions,answers,only_open=False),
                               file_name='Client_Questions_Tracker.csv',mime='text/csv',width='stretch')
        st.caption('The PDF contains only outstanding questions. The CSV also retains answered questions. Keep both with client records; they may contain sensitive financial information.')
    return questions,open_items

def render(p, inspect, register_evidence, suggest):
    cfg=p.config
    if 'guided_stage' not in st.session_state: st.session_state['guided_stage']=0
    if 'guided_files' not in st.session_state: st.session_state['guided_files']=[]
    stage=st.session_state['guided_stage']

    st.header('Start here — your financial reports in 5 steps')
    st.caption('For SMEs preparing management accounts and draft unaudited financial statements. Start with your company, then add its accounting records.')
    issue_panels=[]
    notice = st.session_state.pop('guided_deleted_notice', None)
    if notice:
        st.success(notice)
    parsed=_load_documents(inspect)
    profiles=[(doc,acra) for doc,acra,bank in parsed if acra.get('detected') and acra.get('fields')]
    banks=[bank for doc,acra,bank in parsed if bank.get('detected')]
    # Check once before rendering so tab status reflects restored issue history too.
    records=_issue_records(p,parsed,_bank_batch(parsed,cfg,p.bank))
    statuses=stage_statuses(p,parsed,_bank_batch(parsed,cfg,p.bank),
                            st.session_state.get('guided_files',[]),st.session_state.get('guided_file_decisions',{}))
    labels=tab_labels(STAGES,statuses)
    # Streamlit 1.50 preserves a manually selected tab when only `default` changes.
    # An invisible label identity change makes an explicit navigation action apply
    # its new default, while ordinary reruns keep the user's selected tab.
    suffix='\u200b' if st.session_state.get('guided_navigation_revision',0)%2 else '\u200c'
    labels=[label+suffix for label in labels]
    st.caption('Green ✓ Cleared · Amber ! Needs attention · Grey ○ Not started. Select a tab to review it. Cleared means the current checks passed, not professional approval.')
    tabs=st.tabs(labels, default=labels[stage])

    with tabs[0]:
        st.subheader('Confirm your company details')
        st.write('Start with the business identity and financial year. Enter the details below, or upload an ACRA Business Profile to fill the fields for review.')
        with st.expander('About unaudited financial statements'):
            st.write('Otto supports bookkeeping and draft UFS preparation. Audit exemption, financial-statement preparation and filing requirements are separate matters. [ACRA audit-exemption guidance](https://www.acra.gov.sg/manage/companies/legal-requirements-common-offences/preparing-financial-statements/audit-exemptions/)')
        acra_upload=st.file_uploader('ACRA Business Profile (optional)',type=['pdf'],
            key='guided_acra_upload_'+str(st.session_state.get('guided_upload_version',0)),
            on_change=_go,args=(0,))
        if acra_upload is not None:
            payload=acra_upload.getvalue()
            incoming=[dict(name=acra_upload.name,bytes=payload,sha256=hashlib.sha256(payload).hexdigest())]
            merged=merge_uploads(st.session_state['guided_files'],incoming)
            if [upload_id(f) for f in merged]!=[upload_id(f) for f in st.session_state['guided_files']]:
                st.session_state['guided_files']=merged
                st.rerun()
        if profiles:
            choice=st.selectbox('ACRA profile found',list(range(len(profiles))),format_func=lambda i:profiles[i][0].name)
            doc, result=profiles[choice]
            found=result['fields']
            st.dataframe([{'Field':k.replace('_',' ').title(),'Read from document':v} for k,v in found.items()],hide_index=True,width='stretch')
            if st.button('Use information found in ACRA document',on_click=_go,args=(0,),type='primary'):
                for key in ('company_name','uen','entity_type','registered_address','principal_activity','incorporation_date','fy_end'):
                    if found.get(key):cfg[key]=found[key]
                if found.get('fy_end'):
                    cfg['fy_start']=suggested_start(found['fy_end'],found.get('incorporation_date',''))
                    cfg['fy_confirmed']=False
                cfg['acra_source']={'filename':doc.name,'sha256':doc.sha256,'status':'extracted; director confirmation required'}
                register_evidence(p,doc,'ACRA Business Profile (authenticity not verified)')
                st.success('Fields filled. Check the financial year dates and save below.')
                st.rerun()
            if not found.get('fy_end'):
                st.info('This ACRA profile does not state the financial year-end clearly. Check your previous annual return or ask the company director.')
        else:
            st.caption('You can enter these details manually. An ACRA profile is optional for initial setup.')
        with st.form('guided_company_form'):
            name=st.text_input('Registered company name',cfg.get('company_name',''),placeholder='e.g. EXAMPLE PTE. LTD.')
            uen=st.text_input('UEN (business registration number)',cfg.get('uen',''),placeholder='e.g. 202600000A')
            entity_options=['Private limited company','Sole proprietorship','Partnership']
            entity=st.selectbox('Business type',entity_options,index=entity_options.index(cfg.get('entity_type')) if cfg.get('entity_type') in entity_options else 0)
            addr=st.text_input('Registered address (optional for draft setup)',cfg.get('registered_address',''))
            activity=st.text_input('Main business activity (optional for draft setup)',cfg.get('principal_activity',''))
            st.markdown('**Financial year (important)**')
            st.caption('If this is the company’s first financial year, the start date may be its incorporation date rather than 1 January.')
            ca,cb=st.columns(2)
            with ca:fy_start=st.date_input('Financial year begins',_date(cfg.get('fy_start'),date(2026,1,1)),format='DD/MM/YYYY')
            with cb:fy_end=st.date_input('Financial year ends',_date(cfg.get('fy_end'),date(2026,12,31)),format='DD/MM/YYYY')
            yes=st.checkbox('I checked these dates against company records or confirmed them with the director',value=bool(cfg.get('fy_confirmed')))
            if st.form_submit_button('Save company information',on_click=_go,args=(0,),type='primary'):
                if not name.strip() or not uen.strip():st.error('Please enter both company name and UEN.')
                elif fy_start>fy_end:st.error('The financial year cannot end before it begins.')
                else:
                    changed=(cfg.get('fy_start'),cfg.get('fy_end'))!=(fy_start.isoformat(),fy_end.isoformat())
                    cfg.update(company_name=name.strip(),uen=uen.strip(),entity_type=entity,registered_address=addr,
                               principal_activity=activity,fy_start=fy_start.isoformat(),fy_end=fy_end.isoformat(),fy_confirmed=yes)
                    if changed:
                        cfg['bank_balances_confirmed']=False
                        cfg['bank_balance_source']='Financial year changed: reconfirm bank balances'
                    st.rerun()
        _status('Company information and financial year confirmed',bool(cfg.get('company_name') and cfg.get('uen') and cfg.get('fy_confirmed')),'complete the required fields and tick the date confirmation box')
        st.button('Continue to documents',type='primary',on_click=_go,args=(1,),width='stretch')
        issue_panels.append(st.container())

    with tabs[1]:
        issue_panels.append(st.container())
        st.subheader('Add your accounting documents')
        st.write('Now add bank statements, invoices, receipts and accounting spreadsheets for the company and financial year you set up. Add an ACRA Business Profile here too if you did not provide one under Company.')
        st.caption('Accepted: PDF, Excel (.xlsx, .xls) and CSV. Text-based PDFs work best. Scanned-image PDFs require manual review.')
        upload=st.file_uploader('Choose files or drag them here',type=['pdf','xlsx','xls','csv'],accept_multiple_files=True,
                                key='guided_upload_'+str(st.session_state.get('guided_upload_version',0)),help='Maximum 25 MB per file. Your documents are processed on this Mac, not uploaded to ACRA.',on_change=_go,args=(1,))
        if upload:
            incoming=[]
            for f in upload:
                b=f.getvalue();h=hashlib.sha256(b).hexdigest()
                incoming.append({'name':f.name,'bytes':b,'sha256':h})
            merged=merge_uploads(st.session_state['guided_files'],incoming)
            changed=[upload_id(f) for f in merged]!=[upload_id(f) for f in st.session_state['guided_files']]
            st.session_state['guided_files']=merged
            if changed:st.rerun()
            parsed=_load_documents(inspect)
            profiles=[(doc,acra) for doc,acra,bank in parsed if acra.get('detected') and acra.get('fields')]
            banks=[bank for doc,acra,bank in parsed if bank.get('detected')]
        with st.expander('Want to practice? Load a fictional example instead'):
            st.caption('Two small PDFs: a pretend ACRA profile and a pretend bank statement for a company with a first-year opening balance of S$0. These are NOT real government or bank records.')
            if st.button('Load fictional sample documents',on_click=_go,args=(1,)):
                st.session_state['guided_file_decisions']={}
                sample_dir=Path(__file__).parent/'example_imports'/'guided_demo'
                st.session_state['guided_files']=[{'name':f.name,'bytes':f.read_bytes(),
                        'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(sample_dir.glob('*.pdf'))]
                st.session_state['guided_upload_version']=st.session_state.get('guided_upload_version',0)+1
                st.rerun()
        if parsed:
            st.success(f"{len(parsed)} file(s) received. Here is what I recognised:")
            statuses=[]
            for doc,acra,bank in parsed:
                typ='ACRA company information' if acra.get('detected') and acra.get('fields') else ('Bank statement' if bank.get('detected') else ('Spreadsheet for review' if doc.tables else 'Supporting document / needs review'))
                statuses.append({'File':doc.name,'Identified as':typ,'What happens next':'Review details' if typ in ('ACRA company information','Bank statement') else 'Can be reviewed in Advanced Mode'})
            st.dataframe(statuses,hide_index=True,width='stretch')
        else:
            st.info('No documents added yet. Start by confirming your company in Step 1, then add its records here.')
        _upload_deletion_controls(p, parsed, inspect, 'upload')
        statement_history_controls(p, 'documents', (_go, 1))
        a,b=st.columns([3,1])
        with a:st.button('Continue to bank statements',key='documents_continue_bank',type='primary',width='stretch',on_click=_go,args=(2,))
        with b:
            if st.button('Clear uploaded files',on_click=_go,args=(1,),width='stretch'):
                bank_hashes={doc.sha256 for doc,acra,bank in parsed if bank.get('detected')}
                if _delete_uploads(p, [upload_id(f) for f in st.session_state['guided_files']], bank_hashes):
                    if hasattr(inspect, 'clear'):inspect.clear()
                    st.rerun()
        st.caption('Uploads are stored temporarily in this running session. Use **Save client workspace ZIP** for the accounting data; keep original PDFs/receipts separately.')

    with tabs[2]:
        issue_panels.append(st.container())
        st.subheader('Let the engine check your bank statements')
        st.write('The engine attempts to find **opening balance**, **closing balance**, **statement dates** and **transactions**. It never guesses missing figures.')
        if not cfg.get('fy_confirmed'):
            st.warning('First, confirm your financial year in Step 1. This tells the engine which months to check.')
        if not banks:
            st.warning('No bank statement was recognised. Upload statements under Step 2, or use Advanced Mode for other layouts.')
        else:
            info=[]
            for b in banks:
                info.append({'Statement':b.get('source',''),'Bank':b.get('bank') or 'Not identified',
                             'Account':b.get('masked_account'),'From':b.get('period_start'),'To':b.get('period_end'),
                             'Opening (S$)':b.get('opening'),'Closing (S$)':b.get('closing')})
            st.dataframe(info,hide_index=True,width='stretch')
        _upload_deletion_controls(p, parsed, inspect, 'bank')
        statement_history_controls(p, 'bank', (_go, 2))
        batch=_bank_batch(parsed,cfg,p.bank)
        proposal=batch['balances']
        if banks and cfg.get('fy_confirmed') and proposal['ready']:
            st.success(f"Statements cover your financial year without gaps. Suggested opening balance: **S${proposal['opening']}** · closing balance: **S${proposal['closing']}**.")
            if st.button('Use these verified bank balances',on_click=_go,args=(2,),type='primary',width='stretch'):
                cfg.update(bank_statement_opening=proposal['opening'],bank_statement_closing=proposal['closing'],
                           bank_balances_confirmed=True,bank_balance_source='Bank statement extraction; statement continuity checked',
                           statement_register=batch['detected_banks'])
                for doc,acra,b in parsed:
                    if b.get('detected'):register_evidence(p,doc,'Bank statement')
                st.success('Bank balances saved. Next, review the transactions below.')
                st.rerun()
        elif banks:
            for error in proposal['errors'][:7]:st.warning(error)
            st.caption('If a month is missing, upload it under Step 2. If the bank layout is unusual, use Advanced Mode to enter or map the details safely.')
        if not proposal['ready']:
            with st.expander('I want to enter or verify the two balances myself'):
                with st.form('guided_manual_bank'):
                    op=st.text_input('Opening balance (S$)',str(cfg.get('bank_statement_opening','0.00')))
                    cl=st.text_input('Closing balance (S$)',str(cfg.get('bank_statement_closing','0.00')))
                    checked=st.checkbox('Both amounts are copied from the actual bank statements')
                    if st.form_submit_button('Save verified amounts',on_click=_go,args=(2,)):
                        try:
                            if not checked:raise ValueError('Please verify both values against the statement first.')
                            opval=Decimal(op.replace(',',''));clval=Decimal(cl.replace(',',''))
                            if not opval.is_finite() or not clval.is_finite():raise ValueError('Enter valid amounts.')
                            cfg.update(bank_statement_opening=str(opval),bank_statement_closing=str(clval),
                                       bank_balances_confirmed=True,bank_balance_source='Manually verified against statement')
                            st.rerun()
                        except (InvalidOperation,ValueError) as exc:st.error(str(exc))
        if batch['already_imported']:
            st.success('The transaction rows from these statements are already in your workspace. They will not be imported twice.')
        if batch['rows'] and not batch['already_imported']:
            st.markdown('#### Transactions extracted for your review')
            st.caption('No transactions have been added from these uploaded files unless you explicitly approve them.')
            st.metric('Transactions found',len(batch['rows']))
            display=[{'Date':r['date'],'Description':r['description'],
                      'Money received (S$)':r['deposit'],'Money paid (S$)':r['withdrawal']} for r in batch['rows']]
            st.dataframe(display,width='stretch',hide_index=True)
            problems=batch['issues']+batch['mismatches']
            if batch['duplicates'] and not batch['already_imported']:problems.append(f"{len(batch['duplicates'])} duplicate or previously imported transaction(s).")
            if batch['outside']:problems.append(f"{len(batch['outside'])} transaction(s) fall outside the confirmed financial year.")
            if not proposal['ready']:problems.append('Statements do not establish complete year coverage and balance continuity.')
            for msg in problems[:12]:st.warning(msg)
            if not problems:
                reviewed=st.checkbox('I checked the transactions and totals against my bank statements',
                                      key='guided_import_checked_'+hashlib.sha256(''.join(sorted(b['sha256'] for b in batch['detected_banks'])).encode()).hexdigest()[:12])
                if st.button(f"Import {len(batch['rows'])} reviewed transactions",type='primary',width='stretch',
                             on_click=_go,args=(2,),disabled=not(reviewed and cfg.get('fy_confirmed') and cfg.get('bank_balances_confirmed'))):
                    for row in batch['rows']:
                        if str(row.get('account_code','')).strip() in ('','9999'):
                            row['account_code']=suggest(row) or '9999'
                    p.bank.extend(batch['rows'])
                    for doc,acra,b in parsed:
                        if b.get('detected'):register_evidence(p,doc,'Imported bank transactions')
                    st.success('Transactions imported. Obvious outgoing expense categories were suggested; confirm all categories below.')
                    st.rerun()
            else:st.info('Automatic import is paused for safety. You can correct missing documents or use Advanced Mode for detailed column mapping.')
        elif banks and not batch['already_imported']:
            st.info('No reliable transaction rows were found. This often happens with PDF layouts that have non-standard tables. Try the bank’s CSV/Excel export or Advanced Mode.')
        if p.bank:
            st.markdown('#### Tell us what each transaction was for')
            st.caption('Use the friendly category names, not accounting codes. **Money received is not automatically sales**; director loans and transfers must be classified correctly.')
            by_name={data['name']:code for code,data in COA_MAP.items() if code!='1000'}
            opts=['Not sure / needs review']+list(by_name)
            shown=[]
            for row in p.bank:
                code=str(row.get('account_code','') or '9999')
                label=COA_MAP.get(code,COA_MAP['9999'])['name']
                shown.append({'Date':row.get('date',''),'Description':row.get('description',''),
                              'Money received':row.get('deposit',''),'Money paid':row.get('withdrawal',''),
                              'Category':label if code!='9999' and label in by_name else opts[0]})
            edited=st.data_editor(shown,width='stretch',hide_index=True,num_rows='fixed',disabled=['Date','Description','Money received','Money paid'],
                                  column_config={'Category':st.column_config.SelectboxColumn('What was this for?',options=opts,required=True)},
                                  key='guided_categories_'+str(st.session_state.get('guided_category_revision',0)))
            if st.button('Save these transaction categories',on_click=_go,args=(2,),type='primary'):
                for i,r in enumerate(edited):
                    category=r['Category'];p.bank[i]['account_code']=by_name.get(category,'9999')
                st.session_state['guided_category_revision']=st.session_state.get('guided_category_revision',0)+1
                st.success('Categories saved. Any unsure items will stay flagged for review.')
                st.rerun()
            unresolved=sum(str(r.get('account_code','')) in ('','9999') for r in p.bank)
            if unresolved:st.warning(f'{unresolved} transaction(s) still need a category. Reports will show these as exceptions.')
            else:st.success('Every imported bank transaction has a category. Final validation is still required.')
        if proposal.get('opening') not in (None,'0','0.0','0.00'):
            st.info('For an existing business, non-zero opening bank cash also needs last year’s accounts or an opening trial balance. Bank cash alone does not explain share capital or loans.')
        st.button('Continue to other records',type='primary',on_click=_go,args=(3,),width='stretch')

    with tabs[3]:
        issue_panels.append(st.container())
        st.subheader('Answer outstanding questions')
        _question_panel(p,parsed,_bank_batch(parsed,cfg,p.bank))
        st.divider()
        st.subheader('Check for information not shown on bank statements')
        st.write('The following questions prevent common errors. You can select **Not sure** and resolve them later.')
        question_options=['Not sure','Yes','No']
        questions=[(key,question,hint) for key,question,hint in OTHER_RECORDS]
        responses=cfg.get('simple_questions',{}).copy()
        with st.form('guided_other_records'):
            for key,question,hint in questions:
                current=responses.get(key,'Not sure')
                responses[key]=st.radio(question,question_options,index=question_options.index(current) if current in question_options else 0,
                                        horizontal=True,help=hint,key='question_'+key)
            agree=st.checkbox('I have checked these answers and will provide or record any missing items before the reports are issued.',
                              value=bool(cfg.get('other_records_confirmed',False)))
            if st.form_submit_button('Save my answers',on_click=_go,args=(3,),type='primary'):
                cfg['simple_questions']=responses
                cfg['other_records_confirmed']=bool(agree and all(v!='Not sure' for v in responses.values()))
                if cfg['other_records_confirmed']:
                    st.success('Your checklist has been confirmed.')
                else:
                    st.warning('Answers saved. Complete any Not sure items and tick the confirmation box before generating reports.')
                st.rerun()
        outstanding_records=[q for key,q,_ in questions if cfg.get('simple_questions',{}).get(key,'Not sure')!='No']
        if outstanding_records:
            st.warning('Items marked Yes or Not sure may require additional documents or accounting entries before reports can be completed.')
            for item in outstanding_records:st.write('• '+item)
        if parsed:
            st.markdown('**Save uploaded documents in the evidence list**')
            if st.button('Register all source files as evidence',on_click=_go,args=(3,),width='stretch'):
                for doc,acra,b in parsed:register_evidence(p,doc,'Source document (needs review)')
                st.success('Document filenames and fingerprints recorded. Keep original documents in a secure folder.')
                st.rerun()
        batch=_bank_batch(parsed,cfg,p.bank)
        st.info('To import **director expense spreadsheets**, accounts receivable or manual journals, switch to **Advanced Mode** at the top. The engine provides a preview and column mapper there; it never posts unreviewed files.')
        st.button('Continue to final checks and reports',type='primary',on_click=_go,args=(4,),width='stretch')

    with tabs[4]:
        issue_panels.append(st.container())
        st.subheader('Final review and reports')
        st.write('Here is what is complete, and what still needs attention. Nothing will be labelled approved automatically.')
        result=generate(p)
        if cfg.get('auto_enabled'):
            from auto import current_report
            result,_=current_report(p,inspect)
        questions=build_questions(p,parsed,_bank_batch(parsed,cfg,p.bank))
        remaining=outstanding(questions,cfg.get('clarification_answers',{}))
        crucial=[q for q in remaining if q['priority']=='Required']
        if remaining:
            st.warning(f'{len(remaining)} clarification question(s) are still open, including {len(crucial)} important item(s). Open **Step 4 — Other records** to answer or download the client questions.')
            with st.expander('Questions still waiting for answers',expanded=bool(crucial)):
                for q in remaining:
                    st.write('• '+q['question']+' — '+q['request'])
        else:
            st.success('No unanswered clarification questions remain in this workspace. This is not a professional compliance review.')
        st.download_button('Download outstanding questions to send to client (PDF)',
                           questions_pdf(cfg.get('company_name'),questions,cfg.get('clarification_answers',{})),
                           file_name='Client_Questions_To_Clarify.pdf',mime='application/pdf',width='stretch')
        basics=bool(cfg.get('company_name') and cfg.get('uen') and cfg.get('fy_confirmed'))
        bank_ok=bool(cfg.get('bank_balances_confirmed'))
        classified=bool(p.bank) and all(str(r.get('account_code','') or '9999')!='9999' for r in p.bank)
        _status('Company and financial year',basics,'go to Step 1 to confirm')
        _status('Bank opening and closing balances',bank_ok,'go to Step 3 to review')
        _status('Bank transactions categorised',classified,'go to Step 3 to import and categorise')
        other_ok=bool(cfg.get('other_records_confirmed',False))
        _status('Additional records checklist confirmed',other_ok,'answer every question in Step 4 and confirm records are provided or addressed')
        if cfg.get('simple_questions'):
            unresolved=[k for k,v in cfg['simple_questions'].items() if v!='No']
            if unresolved:st.warning(f'{len(unresolved)} item(s) were answered Yes or Not sure. Ensure the related accounting records have been added or disclosed.')
        if result['errors']:
            st.error(f"Accounting checks found {len(result['errors'])} issue(s). These must be corrected before clean reporting.")
            with st.expander('See each issue and what to fix',expanded=True):
                for err in result['errors']:st.write('• '+str(err))
        else:st.success('Internal arithmetic checks passed. This is not a certification of compliance with Singapore reporting standards.')
        st.markdown('#### Save and download')
        st.download_button('Save editable client workspace (ZIP) — recommended first',p.to_zip(),
                           file_name='Otto_Client_Workspace.zip',mime='application/zip',width='stretch')
        can_export=bool(basics and bank_ok and classified and other_ok and not crucial and not result['errors'] and (p.bank or p.claims or p.journals))
        if not can_export:
            st.warning('Draft report downloads are paused until important clarification questions, the five checklist stages and accounting checks are complete. Advanced Mode can still create clearly labelled working drafts for review.')
        try:
            a,b,c=st.columns(3)
            with a:st.download_button('Management Accounts PDF',management_pdf(result) if can_export else b'',file_name='Management_Accounts_DRAFT.pdf',mime='application/pdf',disabled=not can_export,width='stretch')
            with b:
                can_fs=can_export and cfg.get('entity_type')=='Private limited company'
                st.download_button('Unaudited FS PDF',financial_statements_pdf(result) if can_fs else b'',file_name='Unaudited_FS_DRAFT.pdf',mime='application/pdf',disabled=not can_fs,width='stretch')
            with c:st.download_button('Excel Working Papers',xlsx_report(result) if can_export else b'',file_name='Financial_Workpapers_DRAFT.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',disabled=not can_export,width='stretch')
        except Exception as e:
            st.error(f'Reports could not be prepared: {e}')
        st.caption('Reports are drafts for management/director review. No tax returns, GST returns or ACRA filings are prepared.')
        with st.expander('Additional checks before issuing financial statements'):
            st.write('Confirm reporting framework eligibility, accounting policies, related-party transactions, opening balances, comparative figures, tax provisions, going concern and all required disclosures with a qualified reviewer.')

    records=_issue_records(p,parsed,_bank_batch(parsed,cfg,p.bank))
    for idx,panel in enumerate(issue_panels):
        with panel:
            _attention_panel(p,records,str(idx))
