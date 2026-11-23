"""Synthetic mixed intake documents: profiles never require bank identity."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import unittest
from reportlab.pdfgen import canvas
from streamlit.testing.v1 import AppTest
from engine.bank_intake import analyse_documents
from engine.auto import analyse
from test_bank_intake import package,document
from test_auto_multi import reviewed

ROOT=Path(__file__).resolve().parents[1]

def profile(name='Business Profile.pdf',company='ACME SERVICES PTE. LTD.',uen='202600001A'):
    out=BytesIO();c=canvas.Canvas(out)
    for i,line in enumerate(['ACRA Business Profile', 'Business Profile (Company) of '+company+' ('+uen+')',
                             'Registered Address: 10 EXAMPLE STREET SINGAPORE 123456']):
        c.drawString(45,780-i*20,line)
    c.save();data=out.getvalue()
    return dict(name=name,bytes=data,sha256=sha256(data).hexdigest())

class DocumentRoutingTests(unittest.TestCase):
    def test_profile_has_company_provenance_without_bank_checks_or_mutation(self):
        p=package();before=deepcopy(p.config);f=profile()
        a=analyse_documents([f],p.config);row=a['inventory'][0]
        self.assertEqual(row['type'],'Company profile');self.assertEqual(row['errors'],[])
        self.assertEqual(row['status'],'Review proposed company fields');self.assertEqual(a['groups'],[])
        self.assertTrue(any(v['field']=='uen' for v in row['provenance']))
        self.assertEqual(p.config,before);self.assertEqual(p.bank,[])
        self.assertEqual(analyse([f],p.config)['inventory'][0]['type'],row['type'])

    def test_mixed_uploads_keep_bank_coverage_and_revision_unchanged(self):
        p=package();bank=document();base=analyse_documents([bank],p.config)
        a=analyse_documents([profile(),bank],p.config)
        self.assertEqual(a['groups'],base['groups']);self.assertEqual(len(a['inventory']),2)
        self.assertEqual(a['inventory'][1]['type'],'Bank statement')
        self.assertEqual(a['inventory'][1]['errors'],base['inventory'][0]['errors'])

    def test_mismatch_duplicate_and_unreadable_profiles_are_not_approved(self):
        p=package();f=profile(company='OTHER SERVICES PTE. LTD.',uen='202600002B')
        a=analyse_documents([f,dict(f,name='copy.pdf')],p.config)
        self.assertIn('differs',a['inventory'][0]['errors'][0]);self.assertEqual(a['groups'],[])
        self.assertEqual(a['inventory'][1]['status'],'Excluded exact duplicate')
        data=b'not a PDF';broken=dict(name='Business Profile.pdf',bytes=data,sha256=sha256(data).hexdigest())
        self.assertEqual(analyse_documents([broken],p.config)['inventory'][0]['status'],'Unreadable / unsupported')

    def test_supporting_records_are_retained_but_bad_bank_statements_still_flagged(self):
        p=package();data=b'Description,Amount\nOffice rent,100.00\n'
        f=dict(name='invoice.csv',bytes=data,sha256=sha256(data).hexdigest())
        a=analyse_documents([f,document(bank='CIMB')],p.config)
        self.assertEqual(a['inventory'][0]['type'],'Supporting record / template')
        self.assertEqual(a['inventory'][0]['errors'],[])
        self.assertEqual(a['inventory'][1]['type'],'Bank statement')
        self.assertTrue(any('Bank identity' in e for e in a['inventory'][1]['errors']))

    def test_auto_bank_table_shows_profile_bank_fields_not_applicable(self):
        p,files=reviewed();at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        at.session_state['pkg']=p;at.session_state['guided_files']=[profile()]+files
        at.run();self.assertFalse(at.exception)
        tables=[x.value for x in at.dataframe if {'document_type','bank','account','currency','issues'}<=set(x.value.columns)]
        self.assertEqual(len(tables),1)
        for table in tables:
            row=table.iloc[0]
            self.assertEqual(row['document_type'],'Company profile');self.assertEqual(row['issues'],'')
            for key in ('bank','account','currency'):self.assertEqual(row[key],'Not applicable')
        self.assertEqual(at.session_state['pkg'].bank,p.bank)
