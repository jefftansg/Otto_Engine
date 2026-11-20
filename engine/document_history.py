"""Remove obsolete extraction summaries without erasing accounting provenance."""
import hashlib
import json


def record_id(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()


def remove_statement_history(pkg, selected):
    records = pkg.config.get('statement_register', [])
    selected = set(selected)
    if not selected or not selected.issubset({record_id(r) for r in records}):
        return False
    pkg.config['statement_register'] = [r for r in records if record_id(r) not in selected]
    pkg.config['bank_balances_confirmed'] = False
    pkg.config['bank_balance_source'] = 'Saved statement history removed: reconfirm bank balances'
    return True


def statement_history_controls(pkg, scope, navigate=None):
    import streamlit as st
    records = pkg.config.get('statement_register', [])
    st.markdown('**Saved statement history**')
    st.caption('Extraction summaries saved in your workspace ZIP, not copies of the original PDFs. Removing history keeps recorded transactions, evidence and balance amounts, but requires bank balances to be verified again. Save a new workspace ZIP after removal; older ZIPs keep their original history.')
    if not records:
        st.info('No saved statement history.')
        return
    st.dataframe([{'File': r.get('source', 'Unnamed statement'),
                   'From': r.get('period_start'), 'To': r.get('period_end'),
                   'Status': 'Saved extraction summary'} for r in records],
                 hide_index=True, width='stretch')
    names = {record_id(r): r.get('source', 'Unnamed statement') for r in records}
    selected = st.multiselect('Select obsolete statement history to remove', list(names),
                              format_func=lambda k: names[k] + ' · ' + k[:8],
                              key='history_selection_'+scope)
    args = dict(on_click=navigate[0], args=(navigate[1],)) if navigate else {}
    if st.button('Remove selected statement history', disabled=not selected,
                 key='history_remove_'+scope, **args):
        if remove_statement_history(pkg, selected):
            st.rerun()
