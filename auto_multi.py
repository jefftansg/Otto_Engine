"""Account-aware Auto workflow; the ledger and detailed tools are shared."""
from copy import deepcopy
import streamlit as st
from engine.auto import analyse
from engine.bank_intake import analyse_documents
from engine.auto_multi import issues
from bank_intake_ui import render_intake,render_transfers
from multi_bank_ui import render_details
from engine.core import generate


def render(p,files,inspect,suggest):
    from auto import _setup,_categories,_inbox,_other_records,_reports
    from guided import _upload_deletion_controls
    try:
        a=analyse(files,p.config,inspect)
        banks=analyse_documents(files,p.config,inspect)
    except ValueError as exc:st.error(str(exc));return
    p.config['auto_enabled']=True
    if a['inventory']:
        p.config['auto_inventory']=deepcopy(a['inventory'])
        st.subheader('What Otto found')
        st.dataframe([dict(File=r['name'],Type=r['type'],Status=r['status']) for r in a['inventory']],hide_index=True,width='stretch')
        _upload_deletion_controls(p,a['parsed'],inspect,'auto_multi')
    elif p.config.get('auto_inventory'):
        st.info('Saved source history is available. Re-upload originals in the sidebar to recheck coverage.')
        with st.expander('Saved source inventory — originals unavailable'):st.json(p.config['auto_inventory'])
    _setup(p,a)
    prefix='auto_multi_'+str(st.session_state.get('guided_upload_version',0))+'_'
    render_intake(p,prefix,files=files,analysis=banks)
    render_transfers(p,prefix)
    _categories(p,suggest)
    st.subheader('Bank reconciliation')
    result=generate(p)
    st.dataframe(result['bank_reconciliations'],hide_index=True,width='stretch')
    st.caption('Each account must reconcile independently; internal transfers never become external cash flows or profit.')
    with st.expander('Detailed bank registry, opening journals and other accounting records'):
        st.caption('These tools edit the same ledger as Auto. Supported opening journals need original evidence; no balancing plug is generated.')
        render_details(p,prefix+'details_')
    st.subheader('Review exceptions')
    records,questions=issues(p,a,banks)
    _inbox(p,records,questions)
    _other_records(p)
    a['bank_intake']=banks
    _reports(p,a,records,strict=True)
