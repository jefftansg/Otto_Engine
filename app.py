"""Otto Financial Report Engine v1.2.4: branded, issue-driven guided mode."""
from pathlib import Path
from datetime import date, datetime
import hashlib
import streamlit as st
from engine.core import Package, generate, COA_MAP, money_str, csv_bytes
from engine.importers import (inspect_document, fields, guess_field, convert_records,
                              existing_duplicates, empty_company)
from engine.reports import management_pdf, financial_statements_pdf, xlsx_report
from engine.autofill import extract_acra_profile,extract_bank_statement,consolidate_statement_balances,suggested_start,propose_bank_rows

ROOT = Path(__file__).parent
ASSETS = ROOT / 'assets'
st.set_page_config(
    page_title='Otto | Financial Report Engine',
    page_icon=str(ASSETS / 'otto_icon.png'),
    layout='wide',
)
st.markdown("""<style>
.block-container {padding-top:1.0rem; max-width:1500px}
[data-testid="stMetric"] {background-color:#eff7f8; border-radius:9px; padding:13px}
small {color:#607080}
div[data-testid="stForm"] {border:1px solid #d7e9e9}
.otto-app-title {font-size:2.35rem; font-weight:800; color:#003b57; line-height:1.12; margin:0.04rem 0 0}
.otto-app-subtitle {font-size:1.22rem; font-weight:700; color:#09556c; margin-top:0.12rem}
.otto-app-tagline {font-size:.8rem; text-transform:uppercase; letter-spacing:.13em; font-weight:650; color:#1d9b9c; margin-top:.38rem}
.otto-app-caption {font-size:.77rem; color:#667783; margin:.5rem 0 .9rem}
</style>""",unsafe_allow_html=True)

SAMPLE = ROOT / 'sample_company'
if 'pkg' not in st.session_state:
    st.session_state.pkg=Package(empty_company())
    st.session_state.upload_hash=''
    st.session_state.is_demo=False
p=st.session_state.pkg

hero_image, hero_text = st.columns([1.05, 5.6])
with hero_image:
    st.image(str(ASSETS / 'otto_mascot.png'), width=182)
with hero_text:
    st.markdown('''<div class="otto-app-title">Otto</div>
<div class="otto-app-subtitle">Financial Report Engine</div>
<div class="otto-app-tagline">Clear numbers for a brighter tomorrow</div>
<div class="otto-app-caption">Version 1.2.4 · Bookkeeping · Management Accounts · Financial Statements</div>''',unsafe_allow_html=True)
st.info('Upload your documents, review the details we find, and generate draft reports. Nothing is recorded from an upload without your approval.')
if st.session_state.is_demo:
    st.warning('You are viewing a FICTIONAL demonstration company. Use **Create blank client** in the sidebar to start with your own company.')

with st.sidebar:
    st.image(str(ASSETS / 'otto_wordmark.png'), width=235)
    st.caption('Financial Report Engine · v1.2.4')
    st.divider()
    st.header('Your client')
    if st.button('＋ Start a new company',use_container_width=True,type='primary'):
        st.session_state.pkg=Package(empty_company())
        st.session_state.upload_hash=''
        st.session_state.is_demo=False
        st.session_state['guided_files']=[]
        st.session_state['guided_file_decisions']={}
        st.session_state['guided_stage']=0
        st.session_state['app_mode']='Guided'
        st.session_state['advanced_page']=0
        st.session_state['guided_upload_version']=st.session_state.get('guided_upload_version',0)+1
        st.session_state['guided_category_revision']=st.session_state.get('guided_category_revision',0)+1
        st.session_state.pop('guided_import_checked',None)
        st.session_state.pop('restore_workspace',None)
        st.rerun()
    st.download_button('💾 Save my work (ZIP)',p.to_zip(),file_name='Otto_Client_Workspace.zip',mime='application/zip',use_container_width=True,
        help='Save this ZIP somewhere safe. It contains the accounting data and company settings, but not copies of the original bank statements.')
    st.caption('Save after every working session. You can reload your company later.')
    with st.expander('Restore a saved company or try a demo'):
        upload=st.file_uploader('Open a previously saved workspace ZIP',type=['zip'],
            help='Only for saved workspaces. Upload ACRA records and bank PDFs in Guided Mode.',key='restore_workspace')
        if upload is not None:
            data=upload.getvalue();h=hashlib.sha256(data).hexdigest()
            if h!=st.session_state.upload_hash:
                try:
                    st.session_state.pkg=Package.from_zip(data)
                    st.session_state.upload_hash=h
                    st.session_state.is_demo=False
                    st.session_state['guided_files']=[]
                    st.session_state['guided_file_decisions']={}
                    st.session_state['guided_stage']=0
                    st.session_state['app_mode']='Guided'
                    st.session_state['advanced_page']=0
                    st.session_state['guided_upload_version']=st.session_state.get('guided_upload_version',0)+1
                    st.session_state['guided_category_revision']=st.session_state.get('guided_category_revision',0)+1
                    st.rerun()
                except Exception as exc:st.error(f'Unable to open saved workspace: {exc}')
        if st.button('Open fictional example company',use_container_width=True):
            st.session_state.pkg=Package.from_directory(SAMPLE)
            st.session_state.upload_hash=''
            st.session_state.is_demo=True
            st.session_state['guided_files']=[]
            st.session_state['guided_file_decisions']={}
            st.session_state['guided_stage']=0
            st.session_state['app_mode']='Guided'
            st.session_state['advanced_page']=0
            st.session_state['guided_upload_version']=st.session_state.get('guided_upload_version',0)+1
            st.session_state['guided_category_revision']=st.session_state.get('guided_category_revision',0)+1
            st.session_state.pop('restore_workspace',None)
            st.rerun()
    st.divider()
    st.markdown('**Working mode**')
    if st.session_state.get('app_mode','Guided')=='Advanced':
        st.warning('Professional accounting controls are open. Changes update the same company workspace.')
        if st.button('← Return to Guided Mode',use_container_width=True,type='primary'):
            st.session_state['app_mode']='Guided'
            st.rerun()
    else:
        st.caption('Guided Mode is recommended. The next screen can direct you to professional controls when needed.')
        with st.expander('Professional accounting tools (optional)'):
            st.caption('Use this only to correct journals, director claims or detailed account classifications.')
            if st.button('Open Advanced Mode',use_container_width=True):
                st.session_state['app_mode']='Advanced'
                st.session_state['advanced_page']=1
                st.rerun()
    st.divider()
    st.markdown('**How it works**')
    st.caption('Upload → Company → Bank → Other records → Reports')
    st.caption('PDF, Excel and CSV files are added in Guided Mode. The saved-workspace ZIP above is only for reopening existing work.')
    with st.expander('Privacy and service limits'):
        st.caption('Files are processed locally in the running application. Keep original financial documents separately; source files are not embedded in the saved ZIP.')
        st.caption('Bookkeeping, management accounts and draft unaudited statements only. No corporate tax, GST or ACRA/XBRL filing. No ACRA certification.')


@st.cache_data(show_spinner=False, max_entries=20)
def inspect_cached(filename, payload):
    return inspect_document(filename,payload)


def config_date(value, fallback):
    try:return date.fromisoformat(value)
    except (ValueError,TypeError):return fallback


def register_evidence(pkg,document,doc_type='Supporting document'):
    ref='DOC-'+document.sha256[:10].upper()
    if not any(x.get('evidence_ref')==ref for x in pkg.evidence):
        pkg.evidence.append(dict(evidence_ref=ref,document_type=doc_type,source_file=document.name,
            remarks='Imported locally; source file is not embedded in saved ZIP. SHA-256 '+document.sha256,
            review_status='Pending review'))
    return ref

# All editors use a list of dictionaries so source rows can be saved in a simple portable ZIP.
def edit_table(title,attr,columns,helptext):
    st.subheader(title)
    st.caption(helptext)
    rows=getattr(p,attr)
    if not rows:
        rows=[{col:'' for col in columns}]
    result=st.data_editor(rows,num_rows='dynamic',use_container_width=True,hide_index=True,key=attr+'_editor')
    setattr(p,attr,[{col:str(r.get(col,'') or '') for col in columns} for r in result if any(str(v).strip() for v in r.values())])

def suggest(row):
    text=(row.get('description') or '').lower()
    amt=(row.get('deposit') or '').strip()
    if amt: return ''  # never guess incoming funds as revenue
    if any(x in text for x in ('bank fee','bank charge','service fee','service charge')):return '5100'
    if any(x in text for x in ('facebook','meta ads','google ads','advertising')):return '5300'
    if any(x in text for x in ('hosting','subscription','cloud','software')):return '5400'
    if any(x in text for x in ('office rental','workspace rent','monthly rent')):return '5200'
    return ''

if 'app_mode' not in st.session_state: st.session_state['app_mode']='Guided'
if 'advanced_page' not in st.session_state: st.session_state['advanced_page']=0

if st.session_state['app_mode']=='Guided':
    from guided import render
    render(p,inspect_cached,register_evidence,suggest)
    st.stop()

st.markdown('### Advanced accounting workspace')
st.caption('For detailed review and corrections. All edits use the SAME client workspace as Guided Mode.')
tab_names=['1 · Setup & documents','2 · Dashboard','3 · Bank transactions','4 · Director claims','5 · Manual journals','6 · Receivables','7 · Evidence register','8 · Reports & checks']
page=st.selectbox('Choose the screen to review',list(range(len(tab_names))),
       format_func=lambda i:tab_names[i],key='advanced_page',
       help='Returning to Guided Mode will retain your edits.')
st.divider()
if page==0:
    st.header('Start here · Smart document intake')
    st.caption('Upload existing records first. The engine proposes company details, financial year dates, bank balances and transaction mappings where it can identify them safely.')
    cfg=p.config
    st.markdown('### Step 0 — Upload ACRA profile and bank statements')
    st.caption('Upload any combination of ACRA Business Profile PDF, bank statements in PDF/Excel/CSV, supplier or director expense schedules. You may upload multiple months together. Nothing is silently posted.')
    uploaded=st.file_uploader('Drop ACRA profile, bank statements and accounting files here',
        type=['pdf','xlsx','xls','csv'],accept_multiple_files=True,
        help='Text-based PDFs and spreadsheet exports. Scanned PDFs cannot be read without OCR. Maximum 25 MB per file.',key='source_documents')
    parsed=[]
    if uploaded:
        for up in uploaded:
            try:
                doc=inspect_cached(up.name,up.getvalue())
                acra=extract_acra_profile(doc) if up.name.lower().endswith('.pdf') else {'detected':False,'fields':{}}
                bank=extract_bank_statement(doc)
                parsed.append((doc,acra,bank))
            except Exception as exc:
                st.error(f'{up.name}: {exc}')
        profiles=[(d,a) for d,a,b in parsed if a.get('detected') and (a.get('fields',{}).get('uen') or a.get('fields',{}).get('company_name'))]
        banks=[b for d,a,b in parsed if b.get('detected')]
        st.caption(f'{len(parsed)} file(s) examined · {len(profiles)} ACRA profile candidate(s) · {len(banks)} bank statement candidate(s). Files remain on this computer and are not sent to ACRA.')
        with st.expander('A · Company details from ACRA profile',expanded=bool(profiles)):
            if not profiles:
                st.warning('No ACRA Business Profile fields detected. Upload the text-based ACRA PDF, or complete the company form below. Business Profiles do not always contain an FYE.')
            else:
                selected=st.selectbox('ACRA document',list(range(len(profiles))),format_func=lambda i:profiles[i][0].name,key='v12_selected_acra')
                d,a=profiles[selected]; found=a['fields']
                readable={
                   'company_name':'Company name','uen':'UEN','entity_type':'Business structure',
                   'incorporation_date':'Incorporated / registered','registered_address':'Registered address',
                   'principal_activity':'Principal activity','fy_end':'Financial year-end (if stated)'
                }
                st.dataframe([{'Field':readable.get(k,k),'Extracted value':v,'Source':d.name} for k,v in found.items()],hide_index=True,use_container_width=True)
                for msg in a['warnings']:st.caption('• '+msg)
                if found.get('fy_end'):
                    guess=suggested_start(found['fy_end'],found.get('incorporation_date',''))
                    st.info(f'Proposed 12-month financial period starts {guess} and ends {found["fy_end"]}. The start date is an assumption, not extracted from ACRA; confirm both dates below.')
                replace=st.checkbox('Allow extracted information to replace existing populated fields',value=False,key='v12_replace_company')
                if st.button('Use extracted ACRA details in company form',type='primary',key='v12_use_acra'):
                    for k in ('company_name','uen','entity_type','registered_address','principal_activity','incorporation_date','fy_end'):
                        if found.get(k) and (replace or not cfg.get(k) or k in ('fy_end','incorporation_date')):
                            cfg[k]=found[k]
                    if found.get('fy_end'):
                        if replace or not cfg.get('fy_confirmed'):
                            cfg['fy_start']=suggested_start(found['fy_end'],found.get('incorporation_date',''))
                        cfg['fy_confirmed']=False
                    cfg['acra_source']={'filename':d.name,'sha256':d.sha256,'extracted_fields':list(found.keys()),'status':'proposed - FYE and particulars require user confirmation'}
                    register_evidence(p,d,'ACRA Business Profile (not authenticity verified)')
                    st.success('Extracted details entered as proposals. Confirm financial year dates in Step 1.')
                    st.rerun()
        with st.expander('B · Auto-detect bank opening/closing balances',expanded=bool(banks)):
            if not banks:st.info('No clearly identified bank statement. PDFs must contain selectable text; bank exports may provide a balance summary.')
            else:
                summaries=[{'File':b.get('source'),'Bank':b.get('bank'),'Account':b.get('masked_account'),
                            'Period start':b.get('period_start'),'Period end':b.get('period_end'),
                            'Opening S$':b.get('opening'),'Closing S$':b.get('closing'),
                            'Review items':len(b.get('warnings',[]))} for b in banks]
                st.dataframe(summaries,use_container_width=True,hide_index=True)
                for b in banks:
                    for msg in b.get('warnings',[]):st.caption(f'• {b["source"]}: {msg}')
                proposal=consolidate_statement_balances(banks,cfg.get('fy_start'),cfg.get('fy_end'))
                if proposal['ready']:
                    if proposal.get('opening') not in ('0','0.00','0.0'):
                        st.info('Opening bank cash is not the complete opening trial balance. For an established company, obtain prior-year accounts or a trial balance; the engine cannot infer equity, loans or other opening balances from bank statements alone.')
                    st.success(f'One bank account, complete contiguous FY coverage, consistent monthly balances. Proposed opening S${proposal["opening"]}; closing S${proposal["closing"]}.')
                    if st.button('Use reconciled statement opening and closing balances',type='primary',key='v12_use_balances'):
                        cfg['bank_statement_opening']=proposal['opening'];cfg['bank_statement_closing']=proposal['closing']
                        cfg['bank_balance_source']='Extracted from bank statements, contiguous periods verified'
                        cfg['bank_balances_confirmed']=True
                        cfg['statement_register']=banks
                        for d,a,b in parsed:
                            if b.get('detected'):register_evidence(p,d,'Bank statement: balance extraction')
                        st.success('Bank statement balances populated. Please review the figures and import transactions.')
                        st.rerun()
                else:
                    st.warning('Bank balances not applied automatically: '+ ' | '.join(proposal['errors']))
                    st.info('Upload the missing months or confirm the opening and closing balances in the company form. The engine will not treat incomplete statement coverage as reconciled.')
                if st.button('Save statement extraction register only',key='v12_save_register'):
                    cfg['statement_register']=banks
                    st.success('Statement register saved in client ZIP; the source PDFs themselves are not saved in the ZIP.')
                    st.rerun()
        with st.expander('C · Auto-detect bank transactions (review before import)',expanded=True):
            all_rows=[];import_warnings=[];row_sources=[];statement_mismatches=[]
            for d,a,b in parsed:
                if b.get('detected') or (d.tables and not a.get('detected')):
                    proposed,warns=propose_bank_rows(d)
                    all_rows+=proposed
                    if b.get('detected') and b.get('opening') is not None and b.get('closing') is not None and proposed:
                        from decimal import Decimal
                        net=sum((Decimal(row['deposit'] or '0')-Decimal(row['withdrawal'] or '0') for row in proposed),Decimal('0'))
                        expected=Decimal(b['closing'])-Decimal(b['opening'])
                        if net!=expected:
                            statement_mismatches.append(f'{d.name}: detected transactions net S${net:,.2f}, while the stated balance movement is S${expected:,.2f}.')
                    row_sources.extend([d.name]*len(proposed))
                    import_warnings.extend([f'{d.name}: {msg}' for msg in warns])
            if all_rows:
                st.metric('Transactions automatically identified for review',len(all_rows))
                st.dataframe(all_rows[:100],use_container_width=True,hide_index=True)
                if len(all_rows)>100:st.caption('Showing the first 100 rows. Use the manual mapper below to review full source files.')
                for warning in import_warnings[:25]:st.warning(warning)
                for mismatch in statement_mismatches:st.error('Incomplete or inconsistent extraction — '+mismatch)
                duplicates=existing_duplicates(p.bank,all_rows,'bank')
                if duplicates:st.error(f'{len(duplicates)} transaction(s) match existing workspace rows or repeat within this batch. Resolve duplicates via individual file review; bulk import is disabled.')
                try:
                    beginning=date.fromisoformat(cfg.get('fy_start',''))
                    ending=date.fromisoformat(cfg.get('fy_end',''))
                    outside=[r for r in all_rows if not beginning<=date.fromisoformat(r['date'])<=ending]
                except ValueError:outside=all_rows
                if outside:st.error(f'{len(outside)} transaction(s) outside the financial period. Adjust your FYE or use file-by-file import. Bulk import disabled.')
                deposit=sum((float(r['deposit'] or 0) for r in all_rows),0.0)
                withdrawal=sum((float(r['withdrawal'] or 0) for r in all_rows),0.0)
                st.caption(f'Batch net movement S${deposit-withdrawal:,.2f}; deposits S${deposit:,.2f}; withdrawals S${withdrawal:,.2f}. Every row will start in suspense (9999) unless an account code was in the source.')
                st.warning('Automatic detection is not a guarantee that all source rows were captured. Compare transaction counts and balances against every original statement.')
                reviewed=st.checkbox('I checked original statements against the detected rows, their date/amount/sign and excluded tables. Import these transactions for classification.',key='v12_confirm_rows')
                if st.button('Import reviewed bank transactions',type='primary',key='v12_bulk_import',disabled=not(reviewed and not duplicates and not outside and cfg.get('fy_confirmed') and not import_warnings and not statement_mismatches)):
                    p.bank.extend(all_rows)
                    for d,a,b in parsed:register_evidence(p,d,'Imported bank transaction source')
                    st.success(f'{len(all_rows)} bank transactions imported as unclassified entries. Review tab 3 for coding.')
                    st.rerun()
                if import_warnings or statement_mismatches:st.caption('For excluded rows, statement mismatches or unclear tables, use Step 3 column mapping and manual import instead.')
            else:st.info('No reliable transaction tables with recognised headers were found. You can still map your source columns manually in Step 3.')
        st.markdown('#### Document assistant · What is still needed?')
        needs=[]
        if not profiles and not cfg.get('uen'):
            needs.append('**ACRA Business Profile** — upload a readable PDF to identify the company and its UEN.')
        if not cfg.get('fy_confirmed'):
            needs.append('**Financial year** — confirm the start and end dates below. If absent from the profile, provide the latest ACRA FYE/annual-return information or directors’ confirmation.')
        if not banks:
            needs.append('**Bank records** — upload statements covering the full financial year or download the transaction CSV from your bank.')
        else:
            proposal=consolidate_statement_balances(banks,cfg.get('fy_start'),cfg.get('fy_end'))
            if not proposal['ready']:
                needs.append('**Missing/uncertain bank data** — '+ ' '.join(proposal['errors']))
            elif not cfg.get('bank_balances_confirmed'):
                needs.append('**Bank balances** — use the verified opening/closing values proposed in section B.')
            if proposal.get('opening') and proposal['opening'] not in ('0','0.00','0.0') and not p.journals:
                needs.append('**Previous financial statements / opening trial balance** — a nonzero opening bank balance alone does not explain the opening assets, liabilities and equity.')
        if not p.claims:
            needs.append('**Director/owner-paid expenses** — provide a claim spreadsheet or confirm that none exist.')
        if not p.invoices:
            needs.append('**Outstanding customer invoices** — upload an A/R list or confirm there are no unpaid invoices at year end.')
        if needs:
            for message in needs:st.markdown('- '+message)
        else:st.success('Core document prompts have been addressed. Complete the standard checklist and validation.')
    else:
        st.info('Start by uploading an ACRA Business Profile and monthly bank statements. The engine will inspect and propose what it can read.')

    st.markdown('### Step 1 — Company information and financial year')
    st.info('Financial year-end must be confirmed. Extracted ACRA dates and assumed 12-month financial-year start are suggestions only; select the period actually approved by the company.')
    with st.form('setup_company'):
        ca,cb=st.columns(2)
        with ca:
            name=st.text_input('Registered business name *',value=cfg.get('company_name',''))
            uen=st.text_input('UEN / business registration number *',value=cfg.get('uen',''))
            entities=['Private limited company','Sole proprietorship','Partnership']
            entity=st.selectbox('Business structure',entities,index=entities.index(cfg.get('entity_type')) if cfg.get('entity_type') in entities else 0)
            addr=st.text_input('Registered address',value=cfg.get('registered_address',''))
            activity=st.text_input('Principal business activity',value=cfg.get('principal_activity',''))
        with cb:
            fy_start=st.date_input('Financial year begins *',config_date(cfg.get('fy_start'),date(2026,1,1)),format='DD/MM/YYYY')
            fy_end=st.date_input('Financial year ends *',config_date(cfg.get('fy_end'),date(2026,12,31)),format='DD/MM/YYYY')
            frs=st.selectbox('Reporting framework (management to confirm)', ['SFRS for Small Entities','FRS'],index=0 if cfg.get('reporting_framework')=='SFRS for Small Entities' else 1)
            op=st.text_input('Bank statement opening balance (S$)',value=str(cfg.get('bank_statement_opening','0.00')))
            cl=st.text_input('Bank statement closing balance at financial year-end (S$)',value=str(cfg.get('bank_statement_closing','0.00')))
            bank_confirm=st.checkbox('I have checked both bank balances against the statements',value=bool(cfg.get('bank_balances_confirmed',False)))
            st.caption('Automatically populated from complete contiguous bank statements where possible. Otherwise confirm manually from the statements, not from a guess.')
        a,b,c=st.columns(3)
        with a:fy_confirm=st.checkbox('I have confirmed the financial year dates',value=bool(cfg.get('fy_confirmed',False)))
        with b:framework_ok=st.checkbox('Framework eligibility has been reviewed',value=bool(cfg.get('framework_eligibility_confirmed',False)))
        with c:disclose_ok=st.checkbox('Disclosures have been reviewed',value=bool(cfg.get('disclosures_reviewed',False)))
        submitted=st.form_submit_button('Save company details',type='primary')
    if submitted:
        if fy_start>fy_end:st.error('Financial year start must not be after year end.')
        else:
            old_balances=(str(cfg.get('bank_statement_opening')),str(cfg.get('bank_statement_closing')))
            cfg.update(company_name=name.strip(),uen=uen.strip(),entity_type=entity,
                       registered_address=addr,principal_activity=activity,
                       fy_start=fy_start.isoformat(),fy_end=fy_end.isoformat(),fy_confirmed=fy_confirm,
                       reporting_framework=frs,bank_statement_opening=op,bank_statement_closing=cl,
                       framework_eligibility_confirmed=framework_ok,disclosures_reviewed=disclose_ok,
                       bank_balances_confirmed=bank_confirm)
            if (op,cl)!=old_balances:
                cfg['bank_balance_source']='Manually adjusted; source to be verified' 
            st.success('Company settings saved.');st.rerun()

    st.markdown('#### Directors / funding records')
    st.caption('If directors paid company expenses personally, list their exact names. Use 2100 for the first director, 2101 for the second. Additional loan accounts need a chart-of-accounts extension.')
    directors=p.config.get('directors',[])
    edited_directors=st.data_editor(directors if directors else [{'name':'','loan_account':'2100'}],num_rows='dynamic',hide_index=True,key='setup_directors')
    if st.button('Save director list'):
        p.config['directors']=[dict(name=str(d.get('name','')).strip(),loan_account=str(d.get('loan_account','')).strip()) for d in edited_directors if str(d.get('name','')).strip()]
        st.success('Directors saved.');st.rerun()
    with st.expander('Accounting policies and management statements'):
        with st.form('setup_policies'):
            revenue_policy=st.text_area('Revenue recognition policy',value=cfg.get('revenue_policy',''))
            policies=st.text_area('Accounting policy details',value=cfg.get('accounting_policies',''))
            going=st.text_area('Going concern / director support assessment',value=cfg.get('going_concern_note',''))
            other=st.text_area('Other notes, related parties, comparatives and disclosure matters',value=cfg.get('other_disclosures',''))
            review=st.checkbox('Director review performed',value=bool(cfg.get('director_review_confirmed',False)))
            if st.form_submit_button('Save disclosure notes'):
                cfg.update(revenue_policy=revenue_policy,accounting_policies=policies,going_concern_note=going,
                           other_disclosures=other,director_review_confirmed=review)
                st.rerun()

    st.divider()
    st.markdown('### Step 2 — Document preparation checklist')
    st.caption('Mark each item as Provided, Requested, Not provided or Not applicable. Items below are guidance, not an assertion that every company requires every item.')
    required_docs=[
      ('bank_statements','Bank statements covering the full financial year','Bank PDF/CSV/Excel exports, all accounts; confirm opening and closing balances'),
      ('sales','Sales invoices and revenue receipts','Sales invoices, POS/platform summaries, receipt records'),
      ('purchases','Supplier invoices and expense receipts','Rent, software, advertising, bank charges and other bills'),
      ('director_expenses','Director-paid expenses and reimbursement claims','Expense claim schedule and supporting receipts'),
      ('previous_accounts','Previous-year accounts / opening trial balance','Prior FS or opening ledger balances; first-year entities can mark Not applicable'),
      ('loans','Director loans, share capital and borrowing evidence','Funding confirmations, repayments, share allotment documents'),
      ('receivables','Year-end unpaid customer invoices','A/R list with dates, due dates, partial payments'),
      ('payables','Year-end supplier payables and accruals','Outstanding bills, unpaid costs, accrual schedules'),
      ('other_assets','Assets, deposits, inventory and prepayments','Fixed assets, security deposits, advance payments if applicable'),
      ('confirmations','Management accounting policy and year-end confirmations','FYE, contingencies, related parties, going concern, material subsequent events'),
    ]
    progress=sum(cfg.get('document_checklist',{}).get(k)=='Provided' for k,_,_ in required_docs)
    st.progress(progress/len(required_docs),text=f'{progress} of {len(required_docs)} document categories marked Provided')
    with st.form('document_checklist_form'):
        selections={}
        opts=['Not provided','Requested','Provided','Not applicable']
        for key,label,detail in required_docs:
            x,y=st.columns([2.6,1.0],vertical_alignment='center')
            with x:
                st.markdown('**'+label+'**')
                st.caption(detail)
            with y:
                current=cfg.get('document_checklist',{}).get(key,'Not provided')
                selections[key]=st.selectbox('Status · '+label,opts,index=opts.index(current) if current in opts else 0,label_visibility='collapsed',key='doc_'+key)
        if st.form_submit_button('Save document checklist'):
            cfg['document_checklist']=selections
            st.success('Checklist saved.');st.rerun()

    st.divider()
    st.markdown('### Step 3 — Review and map uploaded PDF, Excel or CSV documents')
    st.caption('Select several files at once. Each file is previewed and mapped before importing; no classification is accepted without your review. The previous ZIP-only restriction has been removed from this section.')
    st.caption('The uploaded documents from Step 0 remain available below for detailed per-file mapping, manual imports and evidence registration.')
    if uploaded:
        names=[f'{i+1}. {u.name}' for i,u in enumerate(uploaded)]
        chosen=st.selectbox('Choose a document to review',list(range(len(uploaded))),format_func=lambda i:names[i])
        file=uploaded[chosen]
        try:
            doc=inspect_cached(file.name,file.getvalue())
            st.success(f'Accepted: {doc.name}  |  {len(doc.tables)} detected table(s)'+(f'  |  {doc.pages} PDF page(s)' if doc.pages else ''))
            for message in doc.notes: st.warning(message)
            kind_label=st.radio('How should this document be used?',
                ['Bank transactions','Director expense claims','Customer receivables','Manual journal entries','Supporting evidence only'],
                horizontal=False,key='purpose_'+doc.sha256[:12])
            kind_map={'Bank transactions':'bank','Director expense claims':'claims',
                      'Customer receivables':'invoices','Manual journal entries':'journals'}
            if kind_label=='Supporting evidence only':
                if st.button('Register document in evidence log',type='primary',key='evid_'+doc.sha256):
                    ref=register_evidence(p,doc,'Supporting document')
                    st.success(f'Registered {doc.name} as {ref}. Keep the original file safely; it is not embedded in the saved workspace ZIP.')
            elif not doc.tables:
                st.error('No usable structured table detected. This file can be registered as supporting evidence, but transactions cannot be posted from it automatically.')
                if st.button('Register as supporting evidence',key='pdf_ev_'+doc.sha256):
                    register_evidence(p,doc,'Unstructured source document')
                    st.success('Registered in evidence log.')
            else:
                table_id=st.selectbox('Select worksheet / PDF-extracted table',list(range(len(doc.tables))),
                     format_func=lambda i: f'{doc.tables[i].label} ({len(doc.tables[i].rows)} rows)',key='table_'+doc.sha256[:12])
                table=doc.tables[table_id]
                top=min(12,len(table.rows))
                header_row=st.number_input('Which row contains column headings?',min_value=1,max_value=max(1,len(table.rows)),value=1,step=1,
                    key=f'header_{doc.sha256[:12]}_{table_id}')
                headers,records=fields(table,header_row)
                st.caption(f'{len(records)} data rows detected. The headings must match the source document; choose another header row if necessary.')
                st.dataframe(records[:12],use_container_width=True,hide_index=True)
                kind=kind_map[kind_label]
                if kind=='bank':
                    mapping_fields=['date','description','reference','deposit','withdrawal','amount','direction','account_code','evidence_ref']
                    st.info('Map separate Deposit / Withdrawal columns where available. For a single signed Amount column, explicitly confirm which sign means money received. All imported rows start in suspense (9999) unless an account-code column exists.')
                elif kind=='claims':mapping_fields=['date','claim_id','director','merchant','description','amount','expense_account','evidence_ref']
                elif kind=='invoices':mapping_fields=['date','invoice_no','due_date','customer','amount','amount_paid','evidence_ref']
                else:mapping_fields=['journal_id','date','account_code','debit','credit','description','evidence_ref']
                st.markdown('#### Column mapping')
                mapping={}; opts=['(not provided)']+headers
                cols=st.columns(3)
                for i,field in enumerate(mapping_fields):
                    guess=guess_field(headers,field)
                    index=opts.index(guess) if guess in opts else 0
                    with cols[i%3]:
                        selected=st.selectbox(field.replace('_',' ').title(),opts,index=index,
                            key=f'map_{doc.sha256[:12]}_{table_id}_{header_row}_{kind}_{field}')
                    mapping[field]='' if selected=='(not provided)' else selected
                signed_mode='positive_deposit'
                if kind=='bank' and mapping.get('amount') and not(mapping.get('deposit') or mapping.get('withdrawal')):
                    signed_mode=st.radio('Single Amount column: positive values represent',
                        ['positive_deposit','positive_withdrawal'],
                        format_func=lambda x:'Money received / deposit' if x=='positive_deposit' else 'Money paid / withdrawal',
                        key='sign_'+doc.sha256[:12])
                if not mapping.get('date') or (kind=='bank' and not(mapping.get('deposit') or mapping.get('withdrawal') or mapping.get('amount'))):
                    st.error('Map a Date column and the required amount columns before importing.')
                else:
                    proposed,issues,skipped=convert_records(records,kind,mapping,doc.name,signed_mode,source_ref='DOC-'+doc.sha256[:10].upper())
                    duplicates=existing_duplicates(getattr(p,kind),proposed,kind)
                    st.markdown('#### Review before posting')
                    st.caption(f'{len(proposed)} proposed rows; {len(issues)} error(s); {len(skipped)} non-transaction / non-date row(s) skipped; {len(duplicates)} duplicate(s).')
                    if issues:
                        for msg in issues[:15]:st.error(msg)
                        if len(issues)>15:st.error(f'... and {len(issues)-15} more errors')
                    if skipped:st.warning('Rows without parseable dates were excluded (source row positions after header): '+', '.join(map(str,skipped[:35]))+(' ...' if len(skipped)>35 else '')+'. Verify excluded rows are headers/totals, not transactions.')
                    if duplicates:st.info('Existing or repeated rows will be skipped, not silently duplicated.')
                    st.dataframe(proposed[:50],use_container_width=True,hide_index=True)
                    confirm=st.checkbox('I checked the row preview, all excluded rows and the column mapping. Add the valid rows to the ledger workspace for classification / reconciliation.',
                        key=f'confirm_{doc.sha256[:12]}_{table_id}_{kind}')
                    can_import=bool(proposed) and not issues and confirm and bool(cfg.get('company_name')) and bool(cfg.get('uen')) and bool(cfg.get('fy_confirmed'))
                    if not cfg.get('fy_confirmed'):
                        st.warning('Complete and confirm the financial year in Step 1 before importing.')
                    if st.button('Import reviewed rows',type='primary',disabled=not can_import,key=f'import_{doc.sha256[:12]}_{table_id}_{kind}'):
                        duplicate_idx=set(duplicates)
                        fresh=[r for i,r in enumerate(proposed) if i not in duplicate_idx]
                        getattr(p,kind).extend(fresh)
                        register_evidence(p,doc,kind_label)
                        st.success(f'{len(fresh)} rows imported. Open the corresponding transaction tab to review coding; validate the statement opening and closing balances.')
                        st.rerun()
            if doc.text_excerpt:
                with st.expander('Preview extracted PDF text (read-only)'):
                    st.text_area('PDF text preview',value=doc.text_excerpt[:7000],height=220,disabled=True)
        except Exception as exc:
            st.error(f'Unable to inspect {file.name}: {exc}')
    else:
        st.info('Drop one or more source documents above. PDFs without reliable transaction tables can still be added to the evidence register.')
    st.markdown('#### Prefer standard CSV layouts? Download blank templates')
    tmpl={
      'bank.csv':['date','description','reference','deposit','withdrawal','account_code','evidence_ref','notes'],
      'claims.csv':['claim_id','date','director','merchant','description','amount','expense_account','evidence_ref','notes'],
      'invoices.csv':['invoice_no','date','due_date','customer','amount','amount_paid','evidence_ref'],
      'journals.csv':['journal_id','date','account_code','debit','credit','description','evidence_ref'],
    }
    dc=st.columns(4)
    for i,(filename,columns) in enumerate(tmpl.items()):
        with dc[i]:st.download_button(filename, csv_bytes([],columns),file_name=filename,mime='text/csv',key='blank_'+filename,use_container_width=True)
    st.divider()
    st.markdown('### Step 4 — Review, validate and export')
    rr=generate(p)
    a,b,c,d=st.columns(4)
    a.metric('Bank transactions',len(p.bank));b.metric('Director claims',len(p.claims))
    c.metric('Supporting evidence',len(p.evidence));d.metric('Blocking checks',len(rr['errors']))
    if rr['errors']:
        st.warning('Outstanding classification, reconciliation and other validation exceptions must be resolved before relying on reports. See **8 · Reports & checks**.')
    else:st.success('Arithmetic checks currently pass. Financial reporting framework and disclosure review are still required.')
    st.caption('Next: review account codes in **3 · Bank transactions**, add missing director claims/journals, and use **8 · Reports & checks** for draft report exports.')

if page==2:
    if st.button('Apply rule-based suggestions to blank / suspense OUTGOING rows'):
        count=0
        for r in p.bank:
            code=str(r.get('account_code','')).strip()
            if code in ('','9999'):
                suggestion=suggest(r)
                if suggestion:r['account_code']=suggestion;count+=1
        st.success(f'Assigned {count} provisional categories. Verify each one.')
    st.caption('Account codes: '+', '.join(f'{c}: {a["name"]}' for c,a in COA_MAP.items()))
    edit_table('Bank transaction classification','bank',['date','description','reference','deposit','withdrawal','account_code','evidence_ref','notes'],
        'Deposit: debit bank, credit selected account. Withdrawal: debit selected account, credit bank. Do not classify director funding as revenue.')
if page==3:
    edit_table('Director-paid expense claims','claims',['claim_id','date','director','merchant','description','amount','expense_account','evidence_ref','notes'],
        'Personal company expenses: debit expense or asset, credit the director loan. Share-capital settlements need separate manual journals.')
if page==4:
    edit_table('Manual double-entry journals','journals',['journal_id','date','account_code','debit','credit','description','evidence_ref'],
        'Each journal ID must have equal debits and credits. Opening balances can be dated before the FY start. Do not double-post bank-sourced transactions.')
if page==5:
    edit_table('Receivables ageing register','invoices',['invoice_no','date','due_date','customer','amount','amount_paid','evidence_ref'],
        'Memo schedule only, NOT auto-posted. For credit sales, add separate double-entry journals; bank receipts against invoices should credit receivables (1100). Outstanding invoice total must equal ledger AR.')
if page==6:
    edit_table('Source evidence log','evidence',['evidence_ref','document_type','source_file','remarks','review_status'],
        'Reference documents stored separately on your computer; the engine stores only their filenames and identifiers.')

r=generate(p)
if page==1:
    st.subheader(p.config.get('company_name','Company'))
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Revenue',f"S${money_str(r['revenue'])}")
    c2.metric('Profit / loss',f"S${money_str(r['profit'])}")
    c3.metric('Total assets',f"S${money_str(r['assets'])}")
    c4.metric('Closing bank balance',f"S${money_str(r['ledger_end'])}")
    a,b,c=st.columns(3)
    a.metric('Liabilities',f"S${money_str(r['liabilities'])}")
    b.metric('Total equity',f"S${money_str(r['equity'])}")
    c.metric('Validation errors',len(r['errors']))
    if r['errors']:st.error('Unresolved errors prevent clean financial reporting. Open Reports & checks.')
    else:st.success('Arithmetic checks passed. This does NOT establish SFRS compliance; review notes and disclosures.')
    st.markdown('**Reporting integrity**: one general ledger drives every report. Individual bank rows and expense claims retain references to their source records.')
if page==7:
    st.subheader('Internal validation')
    st.metric('Blocking errors',len(r['errors']))
    if r['errors']:
        for msg in r['errors']:st.error(msg)
    else:st.success('Core internal arithmetic/reconciliation checks passed.')
    with st.expander(f'{len(r["warnings"])} review items',expanded=True):
        for msg in r['warnings']:st.warning(msg)
    st.markdown('### Export reports')
    st.caption('Outputs always remain DRAFT. PDF exports include a review register. XLSX includes raw sources, ledger, statements and controls.')
    try:
        a,b,c=st.columns(3)
        a.download_button('Management Accounts PDF',management_pdf(r),file_name='Management_Accounts_DRAFT.pdf',mime='application/pdf',use_container_width=True)
        b.download_button('Unaudited FS PDF' if p.config.get('entity_type')=='Private limited company' else 'UFS (company only)',financial_statements_pdf(r) if p.config.get('entity_type')=='Private limited company' else b'',file_name='Unaudited_FS_DRAFT.pdf',mime='application/pdf',use_container_width=True,disabled=p.config.get('entity_type')!='Private limited company')
        c.download_button('Working Papers XLSX',xlsx_report(r),file_name='Financial_Workpapers_DRAFT.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
    except Exception as exc:st.error(f'Export error: {exc}')
    st.caption('Not included: corporate tax computations, IRAS filings, GST, ACRA filing, XBRL creation, audit or automatic issuance of director-approved financial statements.')
