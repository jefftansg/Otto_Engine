"""Explicit manual-entry pilot for multi-bank workspaces.

Do not route these workspaces through the legacy single-account import workflow.
"""
import streamlit as st
from engine.core import generate, COA_MAP
from engine.reports import management_pdf, financial_statements_pdf, xlsx_report
from engine.bank_intake import apply_registry
from bank_intake_ui import render_intake, render_transfers


def render(p):
    prefix='multi_bank_'+str(id(p))+'_'+str(st.session_state.get('guided_upload_version',0))
    st.header('Multi-bank SGD — development pilot')
    st.warning('Working drafts only. Manually stage reviewed bank rows and opening journals. Supported text statements can be identified and grouped locally for review. Cross-date transfers, FX and overdrafts are unsupported. Save original statements separately; workspace ZIPs retain source fingerprints and review records, not original PDFs.')
    c=p.config
    with st.form(prefix+'company'):
        name=st.text_input('Company name',str(c.get('company_name','')))
        uen=st.text_input('UEN',str(c.get('uen','')))
        start=st.text_input('FY start (YYYY-MM-DD)',str(c.get('fy_start','')))
        end=st.text_input('FY end (YYYY-MM-DD)',str(c.get('fy_end','')))
        options=['Private limited company','Sole proprietor']
        entity=st.selectbox('Entity type',options,index=options.index(c['entity_type']) if c.get('entity_type') in options else 0)
        options=['FRS','SFRS for Small Entities']
        framework=st.selectbox('Proposed framework (requires separate eligibility review)',options,index=options.index(c['reporting_framework']) if c.get('reporting_framework') in options else 0)
        fy_confirmed=st.checkbox('I confirm the company identity and reporting dates',value=c.get('fy_confirmed') is True)
        if st.form_submit_button('Apply company details'):
            from datetime import date
            try:
                low,high=date.fromisoformat(start),date.fromisoformat(end)
                if low>high or (high-low).days>732:raise ValueError()
            except ValueError:
                st.error('Enter valid reporting dates, start before end, within two years.');return
            changed=(name,uen,start,end)!=(c.get('company_name'),c.get('uen'),c.get('fy_start'),c.get('fy_end'))
            c.update(company_name=name,uen=uen,fy_start=start,fy_end=end,entity_type=entity,reporting_framework=framework,currency='SGD',fy_confirmed=fy_confirmed)
            if changed:
                for account in c['bank_accounts']:
                    account['confirmed']=False
                    account['coverage_confirmed']=False
            st.success('Company details saved. Recheck bank coverage for changed identity or dates.');st.rerun()
    render_intake(p,prefix)
    c=p.config
    st.subheader('1 · Bank account registry')
    st.caption('Use unique bank codes 1000–1099 and privacy-safe names. Enter independently reviewed opening and closing statement balances. Tick both checks only after manually inspecting original statements and full FY coverage.')
    with st.form(prefix+'registry'):
        columns=['code','name','currency','opening','closing','confirmed','coverage_confirmed']
        rows=[{k:r.get(k,False if k in ('confirmed','coverage_confirmed') else '') for k in columns} for r in c['bank_accounts']]
        if not rows:
            rows=[dict(code='1000',name='',currency='SGD',opening='',closing='',confirmed=False,coverage_confirmed=False)]
        edited=st.data_editor(rows,num_rows='dynamic',hide_index=True,width='stretch',key=prefix+'registry_editor')
        if st.form_submit_button('Apply registry'):
            values=[{k:(r.get(k) is True if k in ('confirmed','coverage_confirmed') else str(r.get(k) or '')) for k in columns} for r in edited if r.get('code') or r.get('name')]
            if apply_registry(p,values):st.success('Registry saved. Validate all accounts before export.');st.rerun()
            else:st.error('Registry rejected: retain accounts used by rows/journals, valid SGD codes, and source-approved balances. Re-analyse statements to change source-approved balances.')
    st.subheader('2 · Reviewed transaction and accounting records')
    st.caption('Use the bank account code for the source account and a separate account_code for the accounting counter-entry. Internal transfers: two same-date rows, opposite equal SGD amounts, counter-account TRANSFER and the same unique transfer_id. Keep bank fees in separate rows.')
    st.caption('Account codes: '+', '.join(code+' '+data['name'] for code,data in COA_MAP.items() if code!='1000'))
    tables=[
        ('Bank transactions','bank',['date','bank_account_code','description','reference','deposit','withdrawal','account_code','transfer_id','evidence_ref','notes','source_sha256','source_row','source_reference']),
        ('Opening / adjusting journals','journals',['journal_id','date','account_code','debit','credit','description','evidence_ref']),
        ('Director claims','claims',['claim_id','date','director','merchant','description','amount','expense_account','evidence_ref','notes']),
        ('Receivables','invoices',['invoice_no','date','due_date','customer','amount','amount_paid','evidence_ref']),
        ('Evidence','evidence',['evidence_ref','document_type','source_file','remarks','review_status'])]
    for label,attr,cols in tables:
        with st.expander(label,expanded=attr=='bank'):
            with st.form(prefix+attr):
                records=getattr(p,attr)
                data=[{k:str(r.get(k,'') or '') for k in cols} for r in records] or [{k:'' for k in cols}]
                edited=st.data_editor(data,num_rows='dynamic',hide_index=True,width='stretch',key=prefix+attr+'_editor',disabled=['source_sha256','source_row','source_reference'] if attr=='bank' else [])
                if st.form_submit_button('Apply '+label.lower()):
                    setattr(p,attr,[{k:str(r.get(k) or '') for k in cols} for r in edited if any(str(v or '').strip() for v in r.values())])
                    st.success('Records saved to current workspace; review validation below.');st.rerun()
    render_transfers(p,prefix)
    c=p.config
    st.subheader('3 · Reconciliation and draft reports')
    r=generate(p)
    st.dataframe(r['bank_reconciliations'],hide_index=True,width='stretch')
    cols=st.columns(3)
    cols[0].metric('Closing bank ledger (SGD)',str(r['ledger_end']))
    cols[1].metric('Profit / loss (SGD)',str(r['profit']))
    cols[2].metric('Blocking errors',len(r['errors']))
    for error in r['errors']: st.error(error)
    for warning in r['warnings']: st.warning(warning)
    if not r['errors']:
        st.info('Arithmetic checks passed for this draft only. Human review and framework/disclosure checks remain required.')
    else:
        st.warning('Resolve blocking errors before downloading pilot accounting reports.')
    if not r['errors']:
        st.download_button('Draft management accounts PDF',management_pdf(r),'Management_Accounts_DRAFT.pdf','application/pdf')
        if c.get('entity_type')=='Private limited company':
            st.download_button('Draft UFS PDF',financial_statements_pdf(r),'UFS_DRAFT.pdf','application/pdf')
        st.download_button('Draft Excel workpapers',xlsx_report(r),'Workpapers_DRAFT.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.download_button('Save pilot workspace ZIP',p.to_zip(),'Otto_Multi_Bank_Workspace.zip','application/zip')
