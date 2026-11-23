"""Upload-first workspace on the same package used by Guided and Advanced."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
import streamlit as st
from engine.auto import analyse, bank_proposal, approve_bank, digest
from engine.auto_classification import validate_proposals, apply_categories, revert_categories, bank_revision
from engine.auto_reports import frozen_report, export_bundle, TEMPLATES
from engine.report_layouts import LAYOUTS
from engine.intake_review import merge_uploads, upload_id
from engine.issue_tracker import sync_issues, update_issue, issues_csv
from engine.attention import build_attention, _item
from engine.clarifications import build_questions, outstanding, OTHER_RECORDS
from engine.core import COA_MAP, generate
from engine.document_history import statement_history_controls
from guided import _upload_deletion_controls


def open_editor(page):
    st.session_state['app_mode']='Advanced'
    st.session_state['advanced_page']=page


def _setup(p,a):
    cfg=p.config
    proposal=a['proposals']
    if a['conflicts']:
        st.warning('Sources disagree on: '+', '.join(a['conflicts'])+'. Confirm the correct company before importing.')
    if cfg.get('fy_confirmed'):
        st.success('Company setup confirmed · '+cfg.get('company_name','')+' · '+cfg.get('fy_start','')+' to '+cfg.get('fy_end',''))
    label='Company setup — confirmed (edit)' if cfg.get('fy_confirmed') else 'Review company and reporting period'
    with st.expander(label, expanded=not cfg.get('fy_confirmed')):
        fields=[f for row in a['inventory'] for f in row['fields'] if f['field'] in ('company_name','uen','fy_end')]
        if fields:st.dataframe(fields,hide_index=True,width='stretch')
        st.caption('Dates on bank statements show their coverage, not necessarily the company’s financial year. Confirm the reporting dates once. Missing information stays unknown.')
        revision=digest({k:cfg.get(k) for k in ('company_name','uen','fy_start','fy_end','fy_confirmed')})[:12]
        with st.form('auto_setup_'+revision):
            name=st.text_input('Company name',cfg.get('company_name') or proposal.get('company_name',{}).get('value',''))
            uen=st.text_input('UEN',cfg.get('uen') or proposal.get('uen',{}).get('value',''))
            start=st.text_input('Reporting period starts (YYYY-MM-DD)',cfg.get('fy_start','') if cfg.get('fy_confirmed') else '')
            end=st.text_input('Reporting period ends (YYYY-MM-DD)',cfg.get('fy_end','') if cfg.get('fy_confirmed') else proposal.get('fy_end',{}).get('value',''))
            entities=['Private limited company','Sole proprietor']
            entity=st.selectbox('Entity type',entities,index=entities.index(cfg['entity_type']) if cfg.get('entity_type') in entities else 0)
            frameworks=['FRS','SFRS for Small Entities']
            framework=st.selectbox('Proposed framework — eligibility requires review',frameworks,index=frameworks.index(cfg['reporting_framework']) if cfg.get('reporting_framework') in frameworks else 0)
            verified=st.checkbox('I reviewed the company identity and reporting dates against its records')
            if st.form_submit_button('Confirm setup',type='primary'):
                try:
                    low,high=date.fromisoformat(start.strip()),date.fromisoformat(end.strip())
                    if not verified or not name.strip() or not uen.strip() or low>high or (high-low).days>732:
                        raise ValueError('Confirm the company, UEN and valid reporting dates.')
                    if (p.bank or p.claims or p.journals or p.invoices) and cfg.get('uen') and uen.strip().upper()!=cfg['uen'].strip().upper():
                        raise ValueError('This workspace already has accounting records. Start a new company to change its UEN.')
                    changed=(name.strip(),uen.strip().upper(),low.isoformat(),high.isoformat())!=(cfg.get('company_name'),cfg.get('uen'),cfg.get('fy_start'),cfg.get('fy_end'))
                    cfg.update(company_name=name.strip(),uen=uen.strip().upper(),fy_start=low.isoformat(),fy_end=high.isoformat(),fy_confirmed=True,entity_type=entity,reporting_framework=framework)
                    if changed:cfg['bank_balances_confirmed']=False
                    if 'bank_accounts' not in cfg and not any((p.bank,p.claims,p.journals,p.invoices,p.evidence)) and any(r['type']=='Bank statement' for r in a['inventory']):
                        cfg['bank_accounts']=[];cfg['auto_enabled']=True
                    st.session_state['auto_setup_notice']='Company setup saved. Next: review bank account identity, coverage and balances.'
                    cfg['auto_setup_provenance']=dict(fields=fields,confirmed_at=date.today().isoformat())
                    st.rerun()
                except ValueError as exc:st.error(str(exc))


def _issues(p,a,proposal):
    questions=outstanding(build_questions(p,a['parsed']),p.config.get('clarification_answers',{}))
    # Bank classification is one review list, not one question plus one issue per row.
    handled=('uncategorised-','company-details-','financial-year-','fye-not-shown-','no-bank-','confirm-balances-')
    questions=[q for q in questions if not q['id'].startswith(handled)]
    items=build_attention(p,questions,generate(p))
    if a['inventory'] and not a['accounts']:
        items.append(_item('auto-no-bank','Upload usable bank statements','No current source can establish bank coverage.',
                           'Upload the bank statements or use Advanced mapping.',severity='Required',source_required=True))
    for account in a['accounts']:
        cov=account['coverage']; details=[m['month']+' '+m['status'] for m in cov['months'] if m['status']!='Covered']+cov['balances']['errors']
        if details:
            items.append(_item('auto-coverage-'+account['id'],'Check coverage for '+account['label'],
                               'Full-year completeness and balance continuity are not yet established.',
                               'Add missing statements or correct the inconsistent source.',severity='Required',details=details,source_required=True))
    problems=[r['name']+': '+' | '.join(r['reasons']) for r in a['inventory']
              if r.get('demo') or r['status']=='Excluded company mismatch' or r['status']=='Needs review']
    if problems:
        items.append(_item('auto-source-review','Review excluded or unreadable files','Some files cannot establish bank evidence.',
                           'Retain as supporting records or remove obsolete files; provide genuine readable bank evidence.',
                           severity='Required',details=problems,source_required=True))
    coverage_errors={e for account in a['accounts'] for e in account['coverage']['balances']['errors']}
    transaction_errors=[e for e in proposal['errors'] if e not in coverage_errors and not e.startswith(('Confirm company identity','Auto posting currently supports'))]
    if transaction_errors and not p.bank and a['accounts']:
        items.append(_item('auto-import','Review transaction extraction','No transactions are posted from uploads without review.',
                           'Resolve the extraction issues or use Advanced mapping.',severity='Required',details=transaction_errors,source_required=True))
    if not a['inventory'] and (p.config.get('auto_inventory') or p.bank or p.claims or p.journals or p.invoices):
        items.append(_item('auto-restored-sources','Re-upload sources to recheck','The workspace keeps source summaries, not original PDFs.',
                           'Add the original source files again to verify coverage.',severity='Required',source_required=True))
    records=sync_issues(p.config,items,sources_available=bool(a['accounts']))
    return records,questions


def _inbox(p,records,questions):
    from clarification_ui import render as clarification_exchange
    clarification_exchange(p,questions)
    active=[r for r in records if r['status']!='Cleared']
    if not active:st.success('No current tracked exceptions. Professional and template approval are still separate.');return
    st.dataframe([dict(Issue=r['title'],Priority=r['severity'],Status=r['status']) for r in active],hide_index=True,width='stretch')
    key=st.selectbox('Exception to resolve',[r['id'] for r in active],format_func=lambda k:next(r['title'] for r in active if r['id']==k),key='auto_exception')
    issue=next(r for r in active if r['id']==key)
    st.write(issue['why'])
    for detail in issue.get('details',[]):st.text('• '+str(detail))
    st.info(issue['question'])
    question=next((q for q in questions if q['id']==issue.get('question_id')),None)
    if question:
        with st.form('auto_answer_'+key):
            response=st.text_area('Answer and supporting evidence')
            status=st.selectbox('Outcome',['Still waiting','Answered','Not applicable'])
            if st.form_submit_button('Save answer'):
                if status!='Still waiting' and not response.strip():st.error('Provide an answer or reason.')
                else:
                    p.config.setdefault('clarification_answers',{})[question['id']]=dict(status='Needs answer' if status=='Still waiting' else status,answer=response.strip())
                    st.rerun()
    with st.form('auto_progress_'+key):
        note=st.text_area('Progress / action taken',value=issue.get('notes',''))
        if st.form_submit_button('Save progress'):
            update_issue(p.config,key,'In progress',note);st.rerun()
    st.button('Open detailed editor for this issue',on_click=open_editor,args=(issue['advanced_page'],),key='auto_issue_editor')
    st.download_button('Download exception register',issues_csv(records),file_name='Otto_Exceptions.csv')
    with st.expander('Resolved history'):
        st.dataframe([dict(Issue=r['title'],Status=r['status'],Notes=r.get('notes','')) for r in records if r['status']=='Cleared'],hide_index=True,width='stretch')


def _categories(p,suggest):
    if not p.bank:return
    st.markdown('#### Review transaction categories')
    st.caption('Enter or edit client replies under Enter client replies directly in Otto below. The Client reply column shows saved replies. Category suggestions require your separate approval.')
    choices={value['name']:key for key,value in COA_MAP.items() if key not in ('1000','9999')}
    if any(r.get('transfer_id') for r in p.bank):choices['Internal transfer (reviewed pair)']='TRANSFER'
    unknown='Needs review';revision=bank_revision(p.bank)
    ai=st.session_state.get('auto_ai_proposals',{})
    ai_rows=ai.get('rows',{}) if ai.get('revision')==revision else {}
    from engine.clarification_workbook import transaction_reply
    from engine.client_replies import suggested_category
    view=[]
    for i,row in enumerate(p.bank):
        reply=transaction_reply(p,row,i)
        client_code=suggested_category(reply)
        suggested=client_code if reply else ai_rows.get(i,{}).get('account_code') or suggest(row)
        saved=row.get('account_code')
        code=saved if saved not in ('','9999',None) else suggested
        view.append(dict(Row=i+1,Date=row.get('date'),Description=row.get('description'),Received=row.get('deposit'),Paid=row.get('withdrawal'),
                         Category='Internal transfer (reviewed pair)' if code=='TRANSFER' and row.get('transfer_id') else COA_MAP.get(code,{}).get('name',unknown),
                         Bank=row.get('bank_account_code','1000'),Reference=row.get('reference',''),
                         Basis='Previously saved' if saved not in ('','9999',None) else 'Client reply suggestion — review required' if client_code else 'Client reply needs category review' if reply else 'Imported AI proposal: '+ai_rows[i]['reason'] if i in ai_rows else 'Local rule suggestion' if suggested else 'Needs evidence',
                         Source=row.get('evidence_ref',''),
                         Client_reply=' | '.join(reply.get(k,'') for k in ('money_type','answer','document') if reply.get(k))))
    edited=st.data_editor(view,hide_index=True,width='stretch',disabled=['Row','Date','Description','Received','Paid','Basis','Source','Bank','Reference','Client_reply'],
                          column_config={'Category':st.column_config.SelectboxColumn(options=[unknown]+list(choices),required=True),'Client_reply':st.column_config.TextColumn('Client reply',width='large')},key='auto_categories_'+revision[:12]+'_'+digest(p.config.get('transaction_clarifications',{}))[:8])
    if st.button('Approve and save reviewed categories',key='auto_save_categories'):
        if apply_categories(p,revision,[choices.get(value['Category'],'9999') for value in edited]):
            st.session_state.pop('auto_report_bundle',None);st.rerun()
        else:st.error('Category approval rejected: source revision changed or a reviewed transfer pair would be altered.')
    history=p.config.get('auto_category_history',[])
    if history:
        with st.expander('Category approval history'):
            st.dataframe([dict(Revision=r['id'][:12],Reverted=r.get('reverted',False)) for r in history],hide_index=True,width='stretch')
            latest=next((r for r in reversed(history) if not r.get('reverted') and r.get('after')==revision),None)
            if latest and st.button('Undo the last category approval'):
                if revert_categories(p,latest['id']):st.rerun()
    with st.expander('Optional AI proposal exchange'):
        st.caption('No cloud provider is connected and Otto sends no financial data to an AI service. An external AI response can be loaded here for validation and review. Exporting this request gives you a local file; share it only with a provider you approve.')
        st.download_button('Download classification review request',json.dumps(dict(ledger_revision=revision,transactions=p.bank),indent=2),file_name='Classification_Review_Request.json')
        response=st.file_uploader('Load AI classification proposals (JSON)',type=['json'],key='auto_ai_response_'+str(st.session_state.get('guided_upload_version',0)))
        if response is not None:
            try:
                if len(response.getvalue())>1024*1024:raise ValueError('AI response exceeds 1 MB.')
                validated=validate_proposals(p.bank,json.loads(response.getvalue()))
                st.dataframe(validated,hide_index=True,width='stretch')
                if st.button('Stage these AI suggestions for review'):
                    st.session_state['auto_ai_proposals']=dict(revision=revision,rows={s['row']:s for s in validated});st.rerun()
            except (ValueError,TypeError) as exc:st.error(str(exc))


def render(p,inspect,register_evidence,suggest,upload_area=None,progress_area=None):
    st.header('Otto Auto')
    st.write('Add documents in the sidebar. Review what needs attention. Download your draft reports.')
    st.caption('Auto preview · Local document analysis · No cloud AI connected · Draft report layouts awaiting template approval')
    notice=st.session_state.pop('auto_setup_notice',None)
    if notice:st.toast(notice,icon='✅')
    files=st.session_state.setdefault('guided_files',[])
    with upload_area if upload_area is not None else st.sidebar:
        st.markdown('**Upload documents**')
        upload=st.file_uploader('Drop bank statements, bookkeeping records and report references here',type=['pdf','csv','xlsx','xls'],accept_multiple_files=True,
                                key='auto_upload_'+str(st.session_state.get('guided_upload_version',0)),help='Up to 50 files, 25 MB per file and 100 MB total. No company form is required before upload.')
        _sidebar_file_controls(p,files,inspect)
    if upload:
        incoming=[dict(name=f.name,bytes=f.getvalue(),sha256=sha256(f.getvalue()).hexdigest()) for f in upload]
        merged=merge_uploads(files,incoming)
        if [upload_id(f) for f in merged]!=[upload_id(f) for f in files]:
            # Validate limits before accepting a batch into the shared upload inventory.
            if len(merged)>50 or sum(len(f['bytes']) for f in merged)>100*1024*1024:
                st.error('Batch limit exceeded: keep at most 50 files and 100 MB.');return
            st.session_state['guided_files']=merged;st.rerun()
    if 'bank_accounts' in p.config:
        from auto_multi import render as render_multi_auto
        render_multi_auto(p,files,inspect,suggest,progress_area=progress_area)
        return
    try:a=analyse(files,p.config,inspect)
    except ValueError as exc:st.error(str(exc));return
    _progress(p,files,a,None,progress_area)
    if a['inventory']:
        p.config['auto_inventory']=deepcopy(a['inventory'])
        st.subheader('What Otto found')
        st.dataframe([{'File':r['name'],'Identified as':r['type'],'Company':r['company'],'Status':r['status'],'Review':'; '.join(r['reasons'])} for r in a['inventory']],hide_index=True,width='stretch')
        with st.expander('Source fields and fingerprints'):
            st.json([dict(file=r['name'],sha256=r['sha256'],fields=r['fields']) for r in a['inventory']])
            selected=st.selectbox('Original source to inspect',list(range(len(files))),format_func=lambda i:files[i]['name'])
            st.download_button('Download selected original source',files[selected]['bytes'],file_name=files[selected]['name'],key='auto_source_download')
    elif p.config.get('auto_inventory') or p.bank or p.claims or p.journals or p.invoices or p.config.get('company_name'):
        st.info('Restored source history is available below. Re-upload the originals to recheck them.')
        with st.expander('Saved source inventory — originals unavailable'):st.json(p.config.get('auto_inventory',[]))
    else:
        st.info('Start by adding your files in the sidebar drop box. Otto will identify the company information and statement coverage it can read.')
        return
    if not any((p.bank,p.claims,p.journals,p.invoices,p.evidence)) and not p.config.get('bank_balances_confirmed'):
        from engine.bank_intake import analyse_documents
        detected=analyse_documents(files,p.config,inspect)
        if detected['groups'] or any(r['type']=='Bank statement' for r in a['inventory']):
            st.info('Otto found bank account groups. Review identity and coverage for each account before staging transactions.')
            _setup(p,a)
            if st.button('Review identified bank accounts',key='auto_enable_multi'):
                p.config['bank_accounts']=[]
                p.config['auto_enabled']=True
                st.rerun()
            return
    p.config['auto_enabled']=True
    _upload_deletion_controls(p,a['parsed'],inspect,'auto')
    with st.expander('Remove obsolete saved statement history'):statement_history_controls(p,'auto')
    _setup(p,a)
    st.subheader('Bank coverage and balances')
    for account in a['accounts']:
        cov=account['coverage']
        st.markdown('**'+account['bank']+' '+account['label']+'**')
        st.write(f"{cov['covered']} of {cov['expected']} reporting months covered")
        if cov['months']:st.dataframe(cov['months'],hide_index=True,width='stretch')
        if cov['opening'] is not None:
            st.write('Proposed opening bank balance: S$'+cov['opening'])
            with st.expander('Opening balance source'):st.json(cov['opening_sources'])
        if cov['latest_closing']:st.write('Latest closing balance: S$'+cov['latest_closing']['value']+' as at '+cov['latest_closing']['date'])
        for msg in cov['balances']['errors']:st.warning(msg)
        if cov['balances']['ready'] and len(a['accounts'])==1:
            checked=st.checkbox('I verified these opening and closing balances against the original statements',key='auto_balance_check_'+a['fingerprint'][:10]+a['context'][:8])
            if st.button('Save reviewed bank balances',disabled=not checked):
                p.config.update(bank_statement_opening=cov['opening'],bank_statement_closing=cov['balances']['closing'],bank_balances_confirmed=True,
                                bank_balance_source='Auto: reviewed statement coverage and balances',statement_register=cov['balances']['rows'])
                st.rerun()
    proposal=bank_proposal(a,p.config,p.bank)
    st.subheader('Review extracted transactions')
    if proposal['rows']:
        st.dataframe(proposal['rows'],hide_index=True,width='stretch')
        for msg in proposal['errors']:st.warning(msg)
        reviewed=st.checkbox('I checked every proposed transaction against the source statements',key='auto_post_review_'+proposal['id'][:12])
        if st.button('Import reviewed transactions',disabled=bool(proposal['errors']) or not reviewed,key='auto_import'):
            if approve_bank(p,a,proposal['id'],reviewed):
                for doc,_,_ in a['parsed']:
                    if any(s['sha256']==doc.sha256 for s in proposal['sources']):register_evidence(p,doc,'Reviewed Auto bank import')
                st.rerun()
    else:st.caption('No unreviewed current-period transaction rows are ready. If a PDF has no reliable table, use the bank CSV/Excel export or the detailed column mapper.')
    _categories(p,suggest)
    st.subheader('Review exceptions')
    records,questions=_issues(p,a,proposal)
    _inbox(p,records,questions)
    _other_records(p)
    _reports(p,a,records,progress_area=progress_area)


def _other_records(p):
    with st.expander('Other records checklist'):
        with st.form('auto_other_records'):
            responses={}
            for key,question,hint in OTHER_RECORDS:
                value=p.config.get('simple_questions',{}).get(key,'Not sure')
                responses[key]=st.radio(question,['Not sure','Yes','No'],index=['Not sure','Yes','No'].index(value),help=hint,horizontal=True)
            checked=st.checkbox('I reviewed the answers and will provide or record all missing items before issue')
            if st.form_submit_button('Save records checklist'):
                p.config['simple_questions']=responses;p.config['other_records_confirmed']=checked and all(v!='Not sure' for v in responses.values());st.rerun()


def _reports(p,a,records,strict=False,progress_area=None):
    st.subheader('Generate and download')
    st.caption('Choose a versioned draft layout. Reference layouts use the supplied reports’ typography as a starting point; exact visual fidelity and owner sign-off are pending. Arial/Liberation Sans are substituted with Helvetica in PDF. Client text, signatures and figures are never copied. DOCX export is not available.')
    for kind,label in (('ma','Management Accounts layout'),('ufs','UFS layout')):
        current=p.config.get('report_layout_'+kind,'classic-v1' if 'bank_accounts' in p.config else ('reference-standard-v1' if kind=='ma' else 'reference-compact-v1'))
        if current not in LAYOUTS:current='classic-v1'
        selected=st.selectbox(label,list(LAYOUTS),index=list(LAYOUTS).index(current),format_func=lambda k:LAYOUTS[k]['name'],key='auto_layout_'+kind)
        p.config['report_layout_'+kind]=selected
    st.caption('All layouts remain drafts pending visual approval. Auto and Advanced use the same selected layouts.')
    try:
        result,meta=frozen_report(p,a,records)
        st.warning(meta['status'])
        if strict:
            for error in result['errors']:st.error(error)
            if result['errors']:st.caption('Correct blocking ledger/source errors before report generation.')
        st.text('Recorded revenue: SGD '+str(result['revenue'])+' · Profit / loss: SGD '+str(result['profit']))
        if st.button('Generate provisional report package',key='auto_generate',disabled=strict and bool(result['errors'])):
            st.session_state['auto_report_bundle']=dict(revision=meta['report_revision'],data=export_bundle(result,meta))
        bundle=st.session_state.get('auto_report_bundle',{})
        _progress(p,st.session_state.get('guided_files',[]),a,a.get('bank_intake'),progress_area,bundle_current=bundle.get('revision')==meta['report_revision'])
        if bundle.get('revision')==meta['report_revision']:
            st.download_button('Download provisional MA, UFS and workpapers',bundle['data'],file_name='Otto_Provisional_Reports.zip',mime='application/zip')
        elif bundle:st.info('Records changed. Generate a new package to use the current ledger snapshot.')
    except (ValueError,KeyError) as exc:st.error('Resolve the setup or ledger issue before report generation: '+str(exc))
    st.download_button('Save Auto workspace ZIP',p.to_zip(),file_name='Otto_Client_Workspace.zip',mime='application/zip')


def current_report(p,inspect):
    """Use the same provisional snapshot controls in every accounting view."""
    files=st.session_state.get('guided_files',[])
    a=analyse(files,p.config,inspect)
    if 'bank_accounts' in p.config:
        from engine.bank_intake import analyse_documents
        from engine.auto_multi import issues
        a['bank_intake']=analyse_documents(files,p.config,inspect)
        records,_=issues(p,a,a['bank_intake'])
    else:records,_=_issues(p,a,bank_proposal(a,p.config,p.bank))
    return frozen_report(p,a,records)



def _progress(p,files,analysis,banks,area,bundle_current=False):
    if area is None:return
    from engine.auto_progress import workflow_progress
    state=workflow_progress(p,files,analysis,banks,bundle_current=bundle_current)
    with area.container():
        st.markdown('**Progress · '+str(state['completed'])+'/'+str(state['total'])+' stages**')
        st.progress(state['completed']/state['total'])
        short={'documents':'Upload','company':'Company','accounts':'Bank','records':'Records','reports':'Drafts'}
        st.caption(' · '.join((':'+('green' if stage['done'] else 'orange' if stage['status']=='Current' else 'gray')+'['+('✓ ' if stage['done'] else '→ ' if stage['status']=='Current' else '○ ')+short[stage['id']]+']') for stage in state['stages']))
        st.markdown('**Now: '+state['current']+'**')
        st.caption('Next: '+state['next'])
        with st.expander('Stage details'):
            for i,stage in enumerate(state['stages'],1):st.caption(str(i)+' '+stage['label']+' · '+stage['status'])
            st.caption('Preparation checks only. Reports remain drafts.')


def _sidebar_file_controls(p,files,inspect):
    notice=st.session_state.pop('guided_deleted_notice',None)
    if notice:st.success(notice)
    if not files:return
    from guided import _delete_uploads
    names={upload_id(f):f['name'] for f in files}
    st.caption(str(len(files))+' uploaded file(s) in this workspace')
    with st.expander('Remove uploaded files'):
        st.caption('Removes session uploads only. Originals on your computer and recorded transactions/evidence are kept.')
        selected=st.multiselect('Select uploaded files to remove',list(names),format_func=lambda k:names[k]+' · '+k[:8],key='auto_remove_'+str(st.session_state.get('guided_upload_version',0)))
        if st.button('Remove selected uploads',disabled=not selected,key='auto_remove_selected'):
            bank_hashes={s.get('sha256') for m in p.config.get('bank_accounts',[]) for s in m.get('statements',[])}
            for f in files:
                if upload_id(f) not in selected:continue
                try:
                    from engine.autofill import extract_bank_statement
                    if extract_bank_statement(inspect(f['name'],f['bytes'])).get('detected'):bank_hashes.add(f['sha256'])
                except Exception:bank_hashes.add(f['sha256'])  # Unreadable sources can still be removed; require recheck.
            if _delete_uploads(p,selected,bank_hashes):
                st.session_state.pop('auto_report_bundle',None)
                st.session_state.pop('auto_ai_proposals',None)
                if hasattr(inspect,'clear'):inspect.clear()
                st.rerun()
