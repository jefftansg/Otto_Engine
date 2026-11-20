"""Ingestion regression tests; no external bank/customer data used."""
import unittest
import io
from engine.importers import (inspect_document,fields,guess_field,convert_records,existing_duplicates,
                              parse_iso_date,parse_money,empty_company)

class ImporterTests(unittest.TestCase):
    def test_csv_headers_and_mapped_bank(self):
        data=(b'Value Date,Transaction Details,Reference,Money In,Money Out,Balance\n'
              b'13/02/2026,Client ABC,TX-1,1500.00,,1500.00\n'
              b'14/02/2026,Bank fee,TX-2,,15.00,1485.00\n')
        d=inspect_document('test.csv',data)
        hs,rs=fields(d.tables[0],1)
        self.assertEqual(guess_field(hs,'deposit'),'Money In')
        mapping={'date':'Value Date','description':'Transaction Details','reference':'Reference','deposit':'Money In','withdrawal':'Money Out'}
        out,errs,skip=convert_records(rs,'bank',mapping,'test.csv',source_ref='DOC-EXAMPLE')
        self.assertEqual((len(out),len(errs),len(skip)),(2,0,0))
        self.assertEqual(out[0]['deposit'],'1500.00')
        self.assertEqual(out[1]['withdrawal'],'15.00')
        self.assertEqual(out[0]['account_code'],'9999')
        self.assertEqual(out[0]['evidence_ref'],'DOC-EXAMPLE')

    def test_signed_amount_and_direction(self):
        records=[{'date':'01/03/2026','amount':'-10','narration':'bank fee'},
                 {'date':'02/03/2026','amount':'500','narration':'cash received'}]
        out,errs,_=convert_records(records,'bank',{'date':'date','amount':'amount','description':'narration'},'test.csv')
        self.assertFalse(errs);self.assertEqual(out[0]['withdrawal'],'10.00')
        self.assertEqual(out[1]['deposit'],'500.00')
        out,errs,_=convert_records(records,'bank',{'date':'date','amount':'amount'},'test.csv',signed_mode='positive_withdrawal')
        self.assertFalse(errs);self.assertEqual(out[1]['withdrawal'],'500.00')

    def test_duplicate_import(self):
        rows=[dict(date='2026-01-01',description='a',reference='1',deposit='10',withdrawal='')]
        self.assertEqual(existing_duplicates(rows,rows,'bank'),[0])

    def test_excel_xlsx_import(self):
        from openpyxl import Workbook
        wb=Workbook();ws=wb.active;ws.title='Bank Account';ws.append(['Date','Description','Credit','Debit'])
        ws.append(['2026-01-01','Customer',100,''])
        io_=io.BytesIO();wb.save(io_)
        d=inspect_document('test.xlsx',io_.getvalue())
        self.assertEqual(d.tables[0].label,'Bank Account')
        self.assertEqual(fields(d.tables[0])[1][0]['Credit'],'100')

    def test_pdf_evidence_text(self):
        from reportlab.pdfgen import canvas
        out=io.BytesIO();pdf=canvas.Canvas(out);pdf.drawString(50,760,'Bank Statement - Demo');pdf.save()
        d=inspect_document('demo.pdf',out.getvalue())
        self.assertEqual(d.pages,1)
        self.assertIn('Bank Statement',d.text_excerpt)
        self.assertEqual(len(d.tables),0)

    def test_unparseable_dates_explicitly_skipped(self):
        out,issues,skipped=convert_records([{'d':'Not a date','a':'100'}],'bank',{'date':'d','amount':'a'},'a.csv')
        self.assertEqual(len(out),0);self.assertEqual(skipped,[1])

    def test_blank_company_unconfirmed(self):
        c=empty_company();self.assertFalse(c['fy_confirmed'])
        self.assertFalse(c['company_name'])

if __name__=='__main__':unittest.main()

class IntegrationImporterTests(unittest.TestCase):
    def test_import_then_reclassify_and_generate_balanced_reports(self):
        from engine.core import Package,generate
        csvdata=b'Date,Details,Credit,Debit\n2026-01-10,Service revenue,200,\n2026-01-11,Service charge,,10\n'
        data=inspect_document('bank.csv',csvdata)
        headers,records=fields(data.tables[0]);mapping={'date':'Date','description':'Details','deposit':'Credit','withdrawal':'Debit'}
        bank,errors,skipped=convert_records(records,'bank',mapping,'bank.csv',source_ref='DOC-ABC')
        self.assertFalse(errors)
        self.assertEqual({row['account_code'] for row in bank},{'9999'})
        bank[0]['account_code']='4000';bank[1]['account_code']='5100'
        cfg=empty_company();cfg.update(company_name='EXAMPLE PTE LTD',uen='EXAMPLE-REG',fy_confirmed=True,bank_statement_closing='190.00')
        pkg=Package(cfg,bank=bank,evidence=[{'evidence_ref':'DOC-ABC','document_type':'Bank statement','source_file':'bank.csv','review_status':'Reviewed'}])
        r=generate(pkg)
        self.assertEqual(r['errors'],[])
        self.assertEqual(str(r['profit']),'190.00')
