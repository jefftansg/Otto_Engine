"""Local statement review and transfer suggestion inbox for the SGD pilot."""
from hashlib import sha256
import streamlit as st
from engine.bank_intake import (analyse_documents,approve_account,staged_rows,approve_import,
                               review_recorded_rows,suggest_transfers,approve_transfer)


def _reset_confirmation(key,revision):
    marker=key+'_revision'
    if st.session_state.get(marker)!=revision:
        st.session_state[key]=False
        st.session_state[marker]=revision


def render_intake(p,prefix,files=None,analysis=None):
    st.subheader('Identify and group bank statements')
    test_mode=p.config.get('synthetic_test_mode') is True
    if test_mode:st.error('SYNTHETIC TEST WORKSPACE: coverage and approvals below assess test fixtures only, not the authenticity of bank-issued statements.')
    st.caption('Upload originals for every account and every reporting month. DBS, OCBC and UOB text statements are supported conservatively. Scans, ambiguous fields and unsupported layouts require source review. Analysis never posts entries.')
    if files is None:
        files=st.file_uploader('Bank statements — PDF, CSV or Excel',type=['pdf','csv','xlsx','xls'],accept_multiple_files=True,help='Maximum 25 MB per file; 50 files and 100 MB per batch. Originals remain local and are not embedded in workspace ZIPs.',key=prefix+'statements')
    if not files:return
    try:
        if analysis is None:
            batch=[dict(name=f.name,bytes=f.getvalue(),sha256=sha256(f.getvalue()).hexdigest()) for f in files]
            analysis=analyse_documents(batch,p.config)
    except ValueError as exc:
        st.error(str(exc));return
    st.dataframe([dict(file=r['name'],status=r['status'],bank=r.get('bank',''),account=r.get('masked_account',''),currency=r.get('currency') or 'Unknown',issues='; '.join(r['errors'])) for r in analysis['inventory']],hide_index=True,width='stretch')
    for row in analysis['inventory']:
        with st.expander('Source fields · '+row['name']):
            if row['provenance']:st.dataframe(row['provenance'],hide_index=True,width='stretch')
            for error in row['errors']:st.warning(error)
    for group in analysis['groups']:
        key=prefix+group['key'];cov=group['coverage']
        _reset_confirmation(key+'source_check',group['revision'])
        _reset_confirmation(key+'link_check',group['revision'])
        with st.expander(group['bank']+' '+group['masked_account']+' · '+('Coverage complete — review required' if not group['errors'] else 'Needs attention'),expanded=True):
            st.write('Account holder: '+(group['company'] or 'Not identified — verify original')+' · Currency: '+(group['currency'] or 'Unknown — verify SGD on original'))
            st.dataframe(cov['months'],hide_index=True,width='stretch')
            st.write('Opening: '+str(cov['opening'])+' · Closing: '+str(cov['closing']))
            for error in group['errors']:st.error(error)
            existing=next((m for m in p.config['bank_accounts'] if m.get('account_key')==group['key']),None)
            free=next((str(i) for i in range(1000,1100) if str(i) not in {str(m.get('code')) for m in p.config['bank_accounts']}),'')
            with st.form(key+'identity'):
                code=st.text_input('Bank control code (1000–1099)',value=existing['code'] if existing else free)
                reviewer=st.text_input('Reviewer name',key=key+'reviewer')
                evidence=st.text_input('Review evidence / original statement location',key=key+'evidence')
                checked=st.checkbox(('I checked the labelled synthetic fixtures for identity, dates and balance continuity (TEST ONLY)' if test_mode else 'I checked the originals: same company, same account, SGD currency, exact reporting coverage and printed balances'),key=key+'source_check')
                link=st.checkbox('If linking an existing manually entered account, I verified that its rows belong to this account',key=key+'link_check')
                if st.form_submit_button('Approve account identity and coverage',disabled=bool(group['errors'])):
                    if approve_account(p,analysis,group['key'],code,group['revision'],reviewer,evidence,checked,link):
                        st.success('Source coverage approved. Opening journals and transaction review are still required.');st.rerun()
                    else:st.error('Approval rejected. Confirm company/reporting dates first; supply reviewer, evidence and all checks. Account mapping must be unique.')
            existing=next((m for m in p.config['bank_accounts'] if m.get('account_key')==group['key']),None)
            if not existing:continue
            proposal=staged_rows(p,analysis,group['key'])
            st.caption('Proposed transactions remain unclassified (9999). Verify every source row and gross deposits/withdrawals; matching net movement alone does not prove completeness.')
            if proposal['rows']:st.dataframe(proposal['rows'],hide_index=True,width='stretch')
            for error in proposal['errors']:st.warning(error)
            _reset_confirmation(key+'rows_check',proposal['revision'])
            with st.form(key+'transactions'):
                reviewer=st.text_input('Transaction reviewer')
                evidence=st.text_input('Transaction review evidence / source location')
                checked=st.checkbox(('I matched the extracted rows to synthetic test fixtures only' if test_mode else 'I matched all transaction dates, gross receipts/payments, references and totals against the originals'),key=key+'rows_check')
                if st.form_submit_button('Approve and stage proposed transactions',disabled=bool(proposal['errors']) or not proposal['rows']):
                    if approve_import(p,analysis,group['key'],proposal['revision'],reviewer,evidence,checked):st.success('Staged once for classification.');st.rerun()
                    else:st.error('Approval rejected; refresh and review the current proposal.')
                if st.form_submit_button('Approve existing rows after manual source review'):
                    if review_recorded_rows(p,existing['code'],reviewer,evidence,checked):st.success('Manual transaction review recorded.');st.rerun()
                    else:st.error('Review rejected: source approval, source references, dates and net movement must agree.')


def render_transfers(p,prefix):
    st.subheader('Review suggested internal transfers')
    candidates=suggest_transfers(p)
    if not candidates:
        st.caption('No unique same-date, equal opposite SGD candidates in unclassified rows. Cross-date, fee-netted and one-to-many movements require separate review.');return
    st.dataframe([{k:v for k,v in c.items() if k not in ('out_index','in_index','id')} for c in candidates],hide_index=True,width='stretch')
    for candidate in candidates:
        with st.form(prefix+'transfer'+candidate['id']):
            st.write(candidate['out_account']+' / '+candidate['out_reference']+' → '+candidate['in_account']+' / '+candidate['in_reference']+' · SGD '+candidate['amount']+' · '+candidate['date'])
            if candidate['ambiguous']:st.warning('Ambiguous: a source row has more than one possible partner. Resolve the source evidence before approval.')
            reviewer=st.text_input('Transfer reviewer')
            evidence=st.text_input('Evidence establishing the internal transfer')
            checked=st.checkbox('I verified both originals and confirm this is one internal transfer, with bank fees recorded separately')
            if st.form_submit_button('Approve this transfer pair',disabled=candidate['ambiguous']):
                if approve_transfer(p,candidate['id'],reviewer,evidence,checked):st.success('Pair approved; amounts and source facts preserved.');st.rerun()
                else:st.error('Approval rejected: candidate changed, is ambiguous, or review evidence is incomplete.')
