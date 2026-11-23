"""Local client clarification workbook preparation, reply preview and human approval."""
import streamlit as st
from hashlib import sha256
from engine.clarification_workbook import prepare_workbook,preview_answers,approve_answers


def render(pkg,questions,prefix='auto'):
    notice=st.session_state.pop('auto_clarification_notice',None)
    if notice and notice['request_id'] in pkg.config.get('clarification_exports',{}):
        st.toast(str(notice['count'])+' clarification replies saved to this workspace.',icon='✅')
    with st.expander('Client clarifications - Excel export and import'):
        st.write('Send the Excel workbook to your client. Ask them to fill in the green cells with the business purpose, money type and supporting document reference. Accounting codes are not required.')
        history=pkg.config.get('clarification_import_history',[])
        if history:st.caption('Last import: '+str(history[-1]['count'])+' answers saved by '+history[-1]['reviewer']+'.')
        if st.button('Prepare clarification workbook',key=prefix+'_prepare_clarifications'):
            try:
                data=prepare_workbook(pkg,questions)
                # This local download is shown only in the matching workspace.
                request_id=next(reversed(pkg.config['clarification_exports']))
                st.session_state['auto_clarification_export_cache']=dict(request_id=request_id,data=data)
            except ValueError as exc:st.error(str(exc))
        ready=st.session_state.get('auto_clarification_export_cache',{})
        if ready.get('request_id') in pkg.config.get('clarification_exports',{}):
            st.download_button('Download client clarification workbook',ready['data'],file_name='Otto_Client_Clarifications.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key=prefix+'_clarification_download')
            st.caption('Save your workspace ZIP after preparing the workbook. It keeps the export record needed to match returned replies.')
        upload=st.file_uploader('Import completed clarification workbook',type=['xlsx'],key=prefix+'_clarification_return_'+str(st.session_state.get('guided_upload_version',0)))
        if upload is None:return
        data=upload.getvalue()
        try:preview=preview_answers(pkg,data)
        except (ValueError,TypeError,KeyError) as exc:
            st.error('Replies were not imported: '+str(exc));return
        if not preview['replies']:
            st.info('No new replies to review. Blank answers remain open; identical replies already saved are not duplicated.');return
        originals=pkg.config['clarification_exports'][preview['request_id']]['items']
        rows=[]
        for reply in preview['replies']:
            item=originals[reply['id']];facts=item['fixed'];transaction=reply['kind']=='Transaction'
            rows.append(dict(Type=reply['kind'],Date=facts[1] if transaction else '',
                Question=facts[3] if transaction else facts[1],Received=facts[4] if transaction else '',Paid=facts[5] if transaction else '',
                Answer=reply['answer'],Money_type=reply['money_type'],Document=reply['document'],Answered_by=reply['answered_by'],Status=reply['status']))
        st.dataframe(rows,hide_index=True,width='stretch')
        st.caption('Saving these replies records client explanations. Transaction categories, transfers, balances and journal entries require their existing separate approval.')
        token=sha256(data).hexdigest()[:12]
        with st.form(prefix+'_approve_clarifications_'+token):
            reviewer=st.text_input('Replies reviewed by')
            checked=st.checkbox('I reviewed these returned answers and want to save them in this company workspace')
            if st.form_submit_button('Approve and save clarification replies'):
                try:
                    if approve_answers(pkg,data,reviewer,checked):
                        st.session_state.pop('auto_report_bundle',None)
                        st.session_state['auto_clarification_notice']=dict(request_id=preview['request_id'],count=len(preview['replies']))
                        st.rerun()
                    else:st.error('Enter the reviewer name and confirm your review before saving replies.')
                except ValueError as exc:st.error('Replies were not saved: '+str(exc))
