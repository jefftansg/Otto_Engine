"""Client Excel replies collect facts; only explicit reviewer approval saves answers."""
from copy import deepcopy
from datetime import date,datetime,timezone
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
from .auto import digest
from .core import money

TX_HEADERS=['Query ID','Date','Bank account','Bank description','Money in (SGD)','Money out (SGD)','Your answer','Money type','Document / receipt reference','Answered by','Response status']
Q_HEADERS=['Query ID','Question','What to provide','Your answer','Document / receipt reference','Answered by','Response status']
STATUSES=['Answered','Need more information','Not applicable']
TYPES=['Sale','Business expense','Loan','Owner funding','Refund','Transfer between own accounts','Other','Not sure','Bank charges','Office / rent','Marketing','Software subscriptions','Professional fees']
SHEETS={'Transactions':(TX_HEADERS,6),'Other questions':(Q_HEADERS,3)}
MAX_ROWS=20000


def context(pkg):
    return digest({k:pkg.config.get(k) for k in ('company_name','uen','fy_start','fy_end','currency')})


def _text(value):return str(value or '').strip()


def _reply(value):
    return {k:_text(value.get(k)) for k in ('answer','money_type','document','answered_by','status')}


def _current(pkg,key):
    value=pkg.config.get('transaction_clarifications' if key.startswith('T-') else 'clarification_answers',{}).get(key,{})
    return _reply(value)


def transaction_key(row,index):
    facts={k:str(row.get(k) or '') for k in ('date','description','reference','deposit','withdrawal','bank_account_code','evidence_ref','source_sha256','source_row','source_reference','transfer_id')}
    return 'T-'+digest(dict(index=index,facts=facts))[:16]


def source_revision(pkg):
    # Accounting category choices may progress while the client is answering.
    return digest([transaction_key(row,i) for i,row in enumerate(pkg.bank)])


def transaction_reply(pkg,row,index):
    return pkg.config.get('transaction_clarifications',{}).get(transaction_key(row,index),{})


def _items(pkg,questions):
    items={}
    accounts={str(m['code']):m.get('name') or m.get('masked_account','') for m in pkg.config.get('bank_accounts',[])}
    for i,row in enumerate(pkg.bank):
        if row.get('account_code') not in (None,'','9999') or row.get('transfer_id'):continue
        key=transaction_key(row,i)
        items[key]=dict(sheet='Transactions',index=i,fixed=[key,row.get('date',''),accounts.get(str(row.get('bank_account_code','1000')),'Business bank account'),
            _text(row.get('description'))[:750],str(money(row.get('deposit'))),str(money(row.get('withdrawal')))])
    for q in questions:
        if q.get('section')=='Transactions' or q['id'].startswith('uncategorised-'):continue
        if pkg.config.get('clarification_answers',{}).get(q['id'],{}).get('status') in ('Answered','Not applicable'):continue
        # Machine/source checks belong with the preparer, not the client's questionnaire.
        if q.get('audience')=='Preparer':continue
        items[q['id']]=dict(sheet='Other questions',fixed=[q['id'],q['question'],q['request']])
    if len(items)>MAX_ROWS:raise ValueError('Too many questions for one workbook. Narrow the review first.')
    return items


def prepare_workbook(pkg,questions):
    """An explicit prepare action registers the exact question/source snapshot."""
    import xlsxwriter
    if pkg.config.get('currency','SGD')!='SGD':raise ValueError('This clarification workbook supports SGD workspaces only.')
    items=_items(pkg,questions)
    if not items:raise ValueError('There are no unanswered client questions or uncategorised transactions.')
    request_id=uuid4().hex
    request=dict(context=context(pkg),bank_revision=source_revision(pkg),items=items,
                 previous={key:_current(pkg,key) for key in items},created_at=datetime.now(timezone.utc).isoformat(timespec='seconds'))
    out=BytesIO();book=xlsxwriter.Workbook(out,{'in_memory':True,'strings_to_formulas':False,'strings_to_urls':False})
    title=book.add_format({'bold':True,'font_size':17,'font_color':'#003B57'})
    heading=book.add_format({'bold':True,'bg_color':'#003B57','font_color':'#FFFFFF','text_wrap':True,'valign':'vcenter'})
    fixed=book.add_format({'font_name':'Arial','font_size':11,'text_wrap':True,'valign':'top','bg_color':'#F2F5F7'})
    entry=book.add_format({'font_name':'Arial','font_size':11,'text_wrap':True,'valign':'top','bg_color':'#E4F3E8'})
    amount=book.add_format({'num_format':'#,##0.00;[Red](#,##0.00);"-"','valign':'top','bg_color':'#F2F5F7'})
    day=book.add_format({'num_format':'dd mmm yyyy','valign':'top','bg_color':'#F2F5F7'})
    for name,(headers,offset) in SHEETS.items():
        sheet=book.add_worksheet(name);sheet.hide_gridlines(2)
        sheet.merge_range(0,1,0,len(headers)-1,'Client clarifications - '+name,title)
        sheet.merge_range(1,1,1,len(headers)-1,_text(pkg.config.get('company_name'))+' | '+_text(pkg.config.get('fy_start'))+' to '+_text(pkg.config.get('fy_end')))
        sheet.merge_range(2,1,2,len(headers)-1,'Fill in the green cells: explain the business purpose, who paid or received the money, and supporting documents.' if name=='Transactions' else 'Answer each question in the green cells and identify any supporting documents. Accounting codes are not required.')
        sheet.merge_range(3,1,3,len(headers)-1,'Keep query IDs and grey source cells unchanged. Partial replies are welcome. Your preparer will review the answers in Otto.')
        sheet.set_row(0,27);sheet.set_row(2,30);sheet.set_row(3,27);sheet.set_row(4,32)
        sheet.write_row(4,0,headers,heading);sheet.freeze_panes(5,2)
        widths=[22,14,18,38,14,14,44,26,30,20,23] if name=='Transactions' else [30,50,48,44,30,20,23]
        for col,width in enumerate(widths):sheet.set_column(col,col,width)
        sheet.set_column(0,0,22,None,{'hidden':True})
        pos=5
        for key,item in items.items():
            if item['sheet']!=name:continue
            lines=max((len(str(v))//max(10,int(widths[col]))+1 for col,v in enumerate(item['fixed']) if col>0),default=4)
            sheet.set_row(pos,min(350,max(72,(lines+1)*14)))
            for col,value in enumerate(item['fixed']):
                if name=='Transactions' and col==1:
                    try:sheet.write_datetime(pos,col,datetime.combine(date.fromisoformat(value),datetime.min.time()),day)
                    except ValueError:sheet.write_string(pos,col,value,fixed)
                elif name=='Transactions' and col in (4,5):sheet.write_number(pos,col,float(Decimal(value)),amount)
                else:sheet.write_string(pos,col,str(value),fixed)
            previous=request['previous'][key]
            fields=['answer','money_type','document','answered_by','status'] if name=='Transactions' else ['answer','document','answered_by','status']
            for col,field in enumerate(fields,offset):
                value=previous.get(field,'')
                if field=='status' and value=='Needs answer':value='Need more information'
                if value:sheet.write_string(pos,col,value,entry)
                else:sheet.write_blank(pos,col,None,entry)
            pos+=1
        if pos>5:
            sheet.autofilter(4,0,pos-1,len(headers)-1)
            sheet.data_validation(5,len(headers)-1,pos-1,len(headers)-1,{'validate':'list','source':STATUSES})
            if name=='Transactions':sheet.data_validation(5,7,pos-1,7,{'validate':'list','source':"='_Otto'!$B$1:$B$"+str(len(TYPES))})
        sheet.set_landscape();sheet.set_paper(9);sheet.fit_to_pages(1,0);sheet.repeat_rows(0,4)
        sheet.set_margins(.3,.3,.4,.4);sheet.print_area(0,0,max(5,pos-1),len(headers)-1)
    meta=book.add_worksheet('_Otto');meta.write_string(0,0,'Otto clarification workbook v1');meta.write_string(1,0,request_id);meta.write_column(0,1,TYPES);meta.very_hidden()
    book.close();pkg.config.setdefault('clarification_exports',{})[request_id]=request
    return out.getvalue()


def _fixed(value,sheet,col):
    if sheet=='Transactions' and col==1:
        if isinstance(value,(datetime,date)):return value.strftime('%Y-%m-%d')
    if sheet=='Transactions' and col in (4,5):return str(money(value))
    return _text(value)


def preview_answers(pkg,data):
    """Never executes formulas or mutates books/config; foreign/stale edits fail closed."""
    from openpyxl import load_workbook
    if len(data)>10*1024*1024:raise ValueError('Workbook exceeds 10 MB.')
    try:
        with ZipFile(BytesIO(data)) as z:
            if len(z.infolist())>2000 or sum(i.file_size for i in z.infolist())>50*1024*1024:raise ValueError('Workbook contents exceed the import limit.')
            if any('vbaProject' in n or 'externalLinks/' in n for n in z.namelist()):raise ValueError('Use the exported .xlsx without macros or external links.')
        book=load_workbook(BytesIO(data),data_only=False,read_only=True,keep_links=False)
    except Exception as exc:raise ValueError('This is not a readable Otto Excel clarification workbook.') from exc
    try:
        if set(book.sheetnames)!=set(SHEETS)|{'_Otto'}:raise ValueError('Workbook tabs changed. Use the original exported workbook.')
        request_id=_text(book['_Otto']['A2'].value)
        request=pkg.config.get('clarification_exports',{}).get(request_id)
        if not request:raise ValueError('This workbook belongs to another workspace or its export record is unavailable. Restore the matching workspace ZIP.')
        if request['context']!=context(pkg):raise ValueError('Company identity, currency or reporting period changed since export. Prepare a fresh workbook before importing replies.')
        if request['bank_revision']!=source_revision(pkg):raise ValueError('Bank transaction source details or row order changed since export. Prepare a fresh workbook before importing replies.')
        seen=set();replies=[]
        for name,(headers,offset) in SHEETS.items():
            sheet=book[name]
            if sheet.max_row>MAX_ROWS+5 or sheet.max_column>len(headers):raise ValueError('Workbook rows/columns changed or exceed the import limit.')
            if [c.value for c in next(sheet.iter_rows(min_row=5,max_row=5,max_col=len(headers)))]!=headers:raise ValueError('Workbook headings changed. Keep the exported columns unchanged.')
            for cells in sheet.iter_rows(min_row=6,max_col=len(headers)):
                if not any(c.value is not None for c in cells):continue
                if any(c.data_type=='f' for c in cells):raise ValueError('Formulas are not accepted in replies. Paste answers as plain text.')
                values=[c.value for c in cells];key=_text(values[0]);item=request['items'].get(key)
                where=name+' row '+str(cells[0].row)
                if not item or key in seen or item['sheet']!=name:raise ValueError('Query matching failed in '+where+'. Keep each exported query once and leave the hidden query column unchanged.')
                seen.add(key)
                for col,expected in enumerate(item['fixed']):
                    if _fixed(values[col],name,col)!=_fixed(expected,name,col):raise ValueError(headers[col]+' changed in '+where+'. Restore the grey source cells; enter explanations only in green cells.')
                fields=['answer','money_type','document','answered_by','status'] if name=='Transactions' else ['answer','document','answered_by','status']
                incoming={field:_text(values[col]) for col,field in enumerate(fields,offset)}
                if any(len(v)>5000 for v in incoming.values()):raise ValueError('A reply exceeds 5,000 characters. Use a supporting document reference.')
                if not any(incoming.values()):continue
                if not incoming.get('answer'):raise ValueError('Add a written explanation in '+where+'.')
                if incoming.get('money_type') and incoming['money_type'] not in TYPES:raise ValueError('Choose a listed money type in '+where+'.')
                incoming.setdefault('money_type','')
                incoming['status']=incoming['status'] or 'Answered'
                if incoming['status'] not in STATUSES:raise ValueError('Choose a listed response status in '+where+'.')
                incoming['status']='Needs answer' if incoming['status']=='Need more information' else incoming['status']
                if incoming.get('money_type')=='Not sure' or incoming['answer'].casefold() in ('not sure','unknown','do not know',"don't know"):
                    incoming['status']='Needs answer'
                current=_current(pkg,key)
                if incoming==current:continue  # Already imported unchanged reply; do not duplicate history.
                if current!=request['previous'][key]:raise ValueError('An answer changed in Otto since this workbook was exported: '+where+'. Review it in Otto before replacing it.')
                replies.append(dict(id=key,kind='Transaction' if name=='Transactions' else 'Question',row=item.get('index'),**incoming))
        if seen!=set(request['items']):raise ValueError('Some exported queries were deleted. Keep all rows; unanswered rows may be left blank.')
        return dict(request_id=request_id,replies=replies)
    except ValueError:raise
    except Exception as exc:raise ValueError('Workbook contents could not be read. Use the original exported Excel file with plain-text replies.') from exc
    finally:book.close()


def approve_answers(pkg,data,reviewer,confirmed=False):
    if not confirmed or not reviewer.strip():return False
    parsed=preview_answers(pkg,data)
    if not parsed['replies']:return False
    cfg=deepcopy(pkg.config);at=datetime.now(timezone.utc).isoformat(timespec='seconds');previous={}
    for row in parsed['replies']:
        store='transaction_clarifications' if row['kind']=='Transaction' else 'clarification_answers'
        target=cfg.setdefault(store,{});previous[row['id']]=deepcopy(target.get(row['id']))
        target[row['id']]=dict(_reply(row),reviewer=reviewer.strip(),reviewed_at=at,export_id=parsed['request_id'])
        if store=='transaction_clarifications':target[row['id']]['row']=row['row']
    cfg.setdefault('clarification_import_history',[]).append(dict(export_id=parsed['request_id'],reviewer=reviewer.strip(),at=at,
        count=len(parsed['replies']),previous=previous,answers=deepcopy(parsed['replies'])))
    pkg.config=cfg
    return True
