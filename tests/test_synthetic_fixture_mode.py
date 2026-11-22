"""Synthetic Test Mode controls.

Fixtures remain labelled and may only be exercised in an explicitly opted-in
sandbox workspace. Ordinary clients must never inherit fixture permissions.
"""
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
import unittest

from engine.auto import analyse, bank_proposal
from engine.bank_intake import analyse_documents
from engine.core import Package
from engine.importers import SourceDocument, SourceTable
from engine.auto_reports import frozen_report, export_bundle


CFG = dict(company_name='SEABREEZE CONSULTING PTE. LTD.',uen='T26ZZ0101A',
           fy_start='2025-12-01',fy_end='2026-11-30',
           fy_confirmed=True,entity_type='Private limited company',
           reporting_framework='FRS')


def fixture(marked=True, name='bank.pdf'):
    marker='SYNTHETIC TEST DATA - NOT OFFICIAL\n' if marked else ''
    text=('OCBC BANK\nSTATEMENT OF ACCOUNT\n'
          'Company Name: SEABREEZE CONSULTING PTE. LTD.\n'
          'Account Number: 1234567890\nAccount Currency: SGD\n'
          'Statement Period: 1 DEC 2025 to 30 NOV 2026\n'
          'BALANCE B/F 0.00\nBALANCE C/F 100.00\n'+marker)
    contents=text.encode()
    item=dict(name=name,bytes=contents,sha256=sha256(contents).hexdigest())
    table=SourceTable('Transactions',[
        ['Date','Description','Reference','Deposit','Withdrawal'],
        ['2025-12-02','Customer payment','PAY-001','100.00','']])
    doc=SourceDocument(name,item['sha256'],[table],text)
    return item,doc


def inspect(mapping):
    return lambda filename,payload: mapping[filename]


class SyntheticFixtureModeTests(unittest.TestCase):
    def test_normal_mode_still_excludes_fictional_bank_evidence(self):
        item,doc=fixture()
        a=analyse([item],CFG,inspect({item['name']:doc}))
        self.assertEqual(a['inventory'][0]['status'],'Excluded from bank evidence')
        self.assertEqual(a['accounts'],[])
        self.assertEqual(analyse_documents([item],CFG,inspect({item['name']:doc}))['groups'],[])

    def test_opted_in_fixture_mode_allows_test_parsing_and_coverage(self):
        item,doc=fixture()
        cfg=dict(CFG,synthetic_test_mode=True)
        a=analyse([item],cfg,inspect({item['name']:doc}))
        self.assertEqual(a['inventory'][0]['type'],'Bank statement')
        self.assertTrue(a['inventory'][0]['demo'])
        self.assertEqual(a['inventory'][0]['authenticity'],'synthetic_fixture')
        self.assertEqual(a['accounts'][0]['coverage']['covered'],12)
        self.assertIn('Synthetic test statement',a['inventory'][0]['status'])
        self.assertEqual(len(bank_proposal(a,cfg,[])['rows']),1)
        b=analyse_documents([item],cfg,inspect({item['name']:doc}))
        self.assertEqual(len(b['groups']),1)
        self.assertEqual(b['groups'][0]['errors'],[])
        self.assertIn('SYNTHETIC TEST',b['inventory'][0]['status'])

    def test_otto_qa_test_institution_is_supported_only_in_test_mode(self):
        item,doc=fixture()
        doc.text_excerpt=doc.text_excerpt.replace('OCBC BANK','OTTO QA TEST FINANCIAL INSTITUTION - TEST ENVIRONMENT')
        item['bytes']=doc.text_excerpt.encode()
        item['sha256']=sha256(item['bytes']).hexdigest()
        doc.sha256=item['sha256']
        test_cfg=dict(CFG,synthetic_test_mode=True)
        a=analyse_documents([item],test_cfg,inspect({item['name']:doc}))
        self.assertEqual(len(a['groups']),1)
        self.assertEqual(a['groups'][0]['bank'],'OTTO TEST BANK')
        self.assertFalse(a['groups'][0]['errors'])
        ordinary=analyse_documents([item],CFG,inspect({item['name']:doc}))
        self.assertEqual(ordinary['groups'],[])

    def test_test_workspace_rejects_unmarked_bank_source(self):
        item,doc=fixture(marked=False)
        cfg=dict(CFG,synthetic_test_mode=True)
        a=analyse([item],cfg,inspect({item['name']:doc}))
        self.assertEqual(a['accounts'],[])
        self.assertIn('Excluded',a['inventory'][0]['status'])
        self.assertEqual(analyse_documents([item],cfg,inspect({item['name']:doc}))['groups'],[])

    def test_tampering_test_flag_invalidates_old_proposal(self):
        item,doc=fixture()
        cfg=dict(CFG,synthetic_test_mode=True)
        a=analyse([item],cfg,inspect({item['name']:doc}))
        self.assertEqual(bank_proposal(a,cfg,[])['errors'],[])
        changed=dict(cfg,synthetic_test_mode=False)
        self.assertTrue(any('Setup changed' in error for error in bank_proposal(a,changed,[])['errors']))

    def test_outputs_remain_marked_synthetic_after_restore(self):
        item,doc=fixture()
        cfg=dict(CFG,synthetic_test_mode=True)
        pkg=Package(cfg)
        a=analyse([item],cfg,inspect({item['name']:doc}))
        result,meta=frozen_report(pkg,a,[])
        self.assertIn('SYNTHETIC TEST',meta['status'])
        self.assertFalse(meta['authorised'])
        self.assertIn('SYNTHETIC TEST',result['auto_report']['status'])
        self.assertTrue(pkg.config['synthetic_test_mode'])
        restored=Package.from_zip(pkg.to_zip())
        self.assertTrue(restored.config['synthetic_test_mode'])
        data=export_bundle(result,meta)
        with ZipFile(BytesIO(data)) as z:
            self.assertTrue(any('SYNTHETIC_TEST_ONLY_' in name for name in z.namelist()))
            pdf=z.read('SYNTHETIC_TEST_ONLY_Management_Accounts_PROVISIONAL.pdf')
            self.assertTrue(pdf.startswith(b'%PDF'))
            book=z.read('SYNTHETIC_TEST_ONLY_Financial_Workpapers_PROVISIONAL.xlsx')
            with ZipFile(BytesIO(book)) as excel:
                strings=excel.read('xl/workbook.xml')
                self.assertIn(b'SYNTHETIC TEST ONLY',strings)


if __name__=='__main__':
    unittest.main()
