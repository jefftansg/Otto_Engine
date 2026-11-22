"""Synthetic bank-identification, coverage, import and transfer acceptance."""
from copy import deepcopy
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
import unittest
from engine.core import Package,generate
from engine.importers import empty_company,inspect_document
from engine.bank_intake import (identify,analyse_documents,approve_account,staged_rows,approve_import,suggest_transfers,
                               approve_transfer,review_recorded_rows,apply_registry)
from test_multi_bank import fixture


CFG=dict(company_name='ACME SERVICES PTE. LTD.',uen='202600001A',fy_start='2025-01-01',fy_end='2025-12-31',fy_confirmed=True,currency='SGD',bank_accounts=[])


def document(bank='OCBC',number='1111110001',start='1 JAN 2025',end='31 DEC 2025',opening='1000.00',closing='1200.00',currency='SGD',name='account-a.csv',transactions=None,owner='ACME SERVICES PTE. LTD.'):
    rows=[['Bank',bank],['Account Number',number],['Account Currency',currency],['Company Name',owner],
          ['Statement Period',start+' TO '+end],['Opening Balance',opening],['Closing Balance',closing],
          ['Date','Description','Reference','Deposit','Withdrawal']]
    rows+=transactions or [['2025-06-01','Customer receipt','R1','200.00','']]
    import csv,io
    out=io.StringIO();csv.writer(out).writerows(rows);payload=out.getvalue().encode()
    return dict(name=name,bytes=payload,sha256=sha256(payload).hexdigest())


def package():return Package(dict(empty_company(),**deepcopy(CFG)))


class BankIntakeTests(unittest.TestCase):
    def test_identifies_supported_banks_normalises_account_without_storing_number(self):
        for bank in ('DBS','OCBC','UOB'):
            a=document(bank=bank,number='111-111-0001')
            row=identify(inspect_document(a['name'],a['bytes']))
            self.assertEqual(row['bank'],bank);self.assertEqual(row['currency'],'SGD');self.assertFalse(row['errors'],row['errors'])
            self.assertEqual(row['masked_account'],'••••0001')
            self.assertNotIn('111-111-0001',str(row))
            b=document(bank=bank,number='1111110001')
            self.assertEqual(row['account_key'],identify(inspect_document(b['name'],b['bytes']))['account_key'])

    def test_same_masked_suffix_different_accounts_and_banks_stay_separate(self):
        docs=[document(),document(number='2222220001',name='b.csv'),document(bank='DBS',name='c.csv')]
        result=analyse_documents(docs,CFG)
        self.assertEqual(len(result['groups']),3)
        self.assertEqual(len({g['key'] for g in result['groups']}),3)

    def test_duplicates_gaps_overlap_boundaries_continuity_and_opening_sources(self):
        a=document(start='1 JAN 2025',end='30 JUN 2025')
        duplicate=dict(a,name='renamed.csv')
        b=document(start='1 JUL 2025',end='31 DEC 2025',opening='1200.00',closing='1400.00',name='b.csv')
        good=analyse_documents([b,a,duplicate],CFG)
        self.assertTrue(good['groups'][0]['coverage']['ready'])
        self.assertEqual(len(good['groups'][0]['coverage']['current']),2)
        self.assertEqual(good['groups'][0]['revision'],analyse_documents([a,b],CFG)['groups'][0]['revision'])
        self.assertEqual(good['inventory'][2]['status'],'Excluded exact duplicate')
        self.assertFalse(analyse_documents([a],CFG)['groups'][0]['coverage']['ready'])
        wrong=document(start='1 AUG 2025',opening='1200.00',closing='1400.00',name='wrong.csv')
        self.assertFalse(analyse_documents([a,wrong],CFG)['groups'][0]['coverage']['ready'])
        mismatch=document(start='1 JUL 2025',opening='1199.00',closing='1400.00',name='wrong.csv')
        self.assertFalse(analyse_documents([a,mismatch],CFG)['groups'][0]['coverage']['ready'])
        prior=document(start='1 DEC 2024',end='31 DEC 2024',opening='800.00',closing='1000.00',name='prior.csv')
        g=analyse_documents([document(),prior],CFG)['groups'][0]
        self.assertEqual(len(g['coverage']['outside']),1);self.assertTrue(g['coverage']['ready'])

    def test_currency_company_demo_masked_and_conflicting_identity_fail_closed(self):
        for source in (document(currency='USD'),document(owner='OTHER SERVICES PTE LTD'),document(name='Fictional_statement.csv')):
            p=package();a=analyse_documents([source],p.config)
            if a['groups']:
                g=a['groups'][0];self.assertFalse(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','Source',True))
            self.assertEqual(p.config['bank_accounts'],[])
        source=document(number='****0001');self.assertEqual(analyse_documents([source],CFG)['groups'],[])

    def test_review_approve_import_idempotent_and_restore(self):
        p=package();a=analyse_documents([document()],p.config);g=a['groups'][0];before=deepcopy(p.config)
        self.assertFalse(approve_account(p,a,g['key'],'1000','stale','Reviewer','Source',True));self.assertEqual(p.config,before)
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','Source',True))
        proposed=staged_rows(p,a,g['key']);self.assertFalse(proposed['errors'],proposed['errors'])
        self.assertEqual(p.bank,[])
        self.assertFalse(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','Source',False))
        self.assertTrue(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','Source',True))
        self.assertEqual(len(p.bank),1);self.assertEqual(p.bank[0]['account_code'],'9999')
        self.assertFalse(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','Source',True));self.assertEqual(len(p.bank),1)
        restored=Package.from_zip(p.to_zip())
        self.assertEqual(restored.bank,p.bank)
        self.assertEqual(staged_rows(restored,a,g['key'])['rows'],[])
        self.assertFalse(any('source coverage approval' in e.lower() or 'source transaction review' in e.lower() for e in generate(restored)['errors']))
        restored.bank[0]['deposit']='201.00'
        self.assertTrue(any('review is missing or stale' in e for e in generate(restored)['errors']))

    def test_registry_edits_preserve_metadata_and_cannot_orphan_posted_accounts(self):
        p=package();a=analyse_documents([document()],p.config);g=a['groups'][0]
        approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','Source',True)
        meta=deepcopy(p.config['bank_accounts'][0]);self.assertTrue(apply_registry(p,[dict(meta,name='Privacy-safe label')]))
        self.assertEqual(p.config['bank_accounts'][0]['statements'],meta['statements'])
        p.bank=[dict(bank_account_code='1000',date='2025-01-02')]
        before=deepcopy(p.config);self.assertFalse(apply_registry(p,[]));self.assertEqual(before,p.config)
        changed=dict(p.config['bank_accounts'][0],closing='1300.00')
        self.assertFalse(apply_registry(p,[changed]));self.assertEqual(D(p.config['bank_accounts'][0]['closing']),D('1200'))

    def test_pdf_provenance_page_and_unsupported_image_file(self):
        from reportlab.pdfgen import canvas
        out=BytesIO();c=canvas.Canvas(out)
        for i,line in enumerate(['OCBC Bank','STATEMENT OF ACCOUNT','Account No: 1111110001','Currency: SGD','Company Name: ACME SERVICES PTE. LTD.','Statement Period: 1 JAN 2025 TO 31 DEC 2025','Opening Balance: 1000.00','Closing Balance: 1200.00']):c.drawString(45,780-i*20,line)
        c.save();payload=out.getvalue();row=identify(inspect_document('statement.pdf',payload))
        self.assertTrue(all(f['page']==1 for f in row['provenance'] if f['excerpt']))
        result=analyse_documents([dict(name='bad.pdf',bytes=b'not a pdf',sha256=sha256(b'not a pdf').hexdigest())],CFG)
        self.assertEqual(result['inventory'][0]['status'],'Unreadable / unsupported')


class TransferSuggestionTests(unittest.TestCase):
    def candidate(self):
        p=fixture()
        for r in p.bank:
            if r.get('transfer_id'):r['transfer_id']='';r['account_code']='9999'
        return p

    def test_suggestion_never_posts_without_review_then_pairs_once(self):
        p=self.candidate();before=deepcopy(p.bank);choices=suggest_transfers(p)
        self.assertEqual(p.bank,before);self.assertEqual(len(choices),1);self.assertFalse(choices[0]['ambiguous'])
        self.assertFalse(approve_transfer(p,choices[0]['id'],'Reviewer','Source',False));self.assertEqual(before,p.bank)
        self.assertTrue(approve_transfer(p,choices[0]['id'],'Reviewer','Original bank evidence',True))
        r=generate(p);self.assertFalse(r['errors'],r['errors']);self.assertEqual(r['cashflows']['Operating'],D('300'))
        self.assertEqual(r['profit'],D('300'));self.assertEqual(len([e for e in r['entries'] if e['source']=='Bank transfer']),2)
        self.assertFalse(approve_transfer(p,choices[0]['id'],'Reviewer','Source',True))
        restored=Package.from_zip(p.to_zip());self.assertEqual(generate(restored)['entries'],r['entries'])

    def test_ambiguity_fees_cross_dates_and_edits_do_not_auto_pair(self):
        p=self.candidate();p.bank.append(dict(p.bank[2],reference='Other receipt'))
        choices=suggest_transfers(p);self.assertTrue(all(c['ambiguous'] for c in choices))
        self.assertFalse(approve_transfer(p,choices[0]['id'],'Reviewer','Source',True))
        for field,value in (('date','2025-06-02'),('deposit','299')):
            p=self.candidate();p.bank[2][field]=value;self.assertEqual(suggest_transfers(p),[])
        p=self.candidate();choice=suggest_transfers(p)[0];approve_transfer(p,choice['id'],'Reviewer','Source',True)
        p.bank[2]['description']='Changed source after review'
        self.assertTrue(any('stale' in e for e in generate(p)['errors']))
        self.assertFalse(any(e['source']=='Bank transfer' for e in generate(p)['entries']))


class CoverageLifecycleTests(unittest.TestCase):
    def test_overlap_foreign_period_missing_month_and_prior_evidence(self):
        a=document(start='1 JAN 2025',end='30 JUN 2025')
        overlap=document(start='1 JUN 2025',opening='1200.00',closing='1400.00',name='b.csv')
        self.assertTrue(any('overlapping' in e for e in analyse_documents([a,overlap],CFG)['groups'][0]['errors']))
        extended=document(start='1 DEC 2024')
        self.assertFalse(analyse_documents([extended],CFG)['groups'][0]['coverage']['ready'])
        eleven=document(start='1 FEB 2025')
        cov=analyse_documents([eleven],CFG)['groups'][0]['coverage']
        self.assertFalse(cov['ready']);self.assertEqual(cov['months'][0]['status'],'Missing / incomplete')
        prior=document(start='1 DEC 2024',end='31 DEC 2024',closing='999.00',name='prior.csv')
        g=analyse_documents([document(),prior],CFG)['groups'][0]
        self.assertTrue(any('Previous-period closing conflicts' in e for e in g['errors']))
        self.assertFalse(analyse_documents([prior],CFG)['groups'][0]['coverage']['ready'])

    def test_account_reviews_invalidate_on_company_dates_source_changes_and_keep_history(self):
        p=package();a=analyse_documents([document()],p.config);g=a['groups'][0]
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'First reviewer','Original',True))
        q=staged_rows(p,a,g['key']);self.assertTrue(approve_import(p,a,g['key'],q['revision'],'Reviewer','Original',True))
        self.assertTrue(review_recorded_rows(p,'1000','Second reviewer','Recheck',True))
        self.assertEqual(p.config['bank_review_history'][0]['record']['reviewer'],'Reviewer')
        restored=Package.from_zip(p.to_zip());self.assertEqual(restored.config['bank_review_history'],p.config['bank_review_history'])
        for field,value in (('company_name','OTHER PTE LTD'),('uen','OTHER'),('fy_end','2025-11-30'),('fy_confirmed',False)):
            changed=deepcopy(p);changed.config[field]=value
            self.assertTrue(any('stale' in e for e in generate(changed)['errors']))
        corrupt=Package.from_zip(p.to_zip());corrupt.config['bank_accounts'][0]['statements'][0]['opening']='corrupt'
        self.assertTrue(any('Invalid saved statement balances' in e for e in generate(corrupt)['errors']))
        changed=analyse_documents([document(closing='1250.00')],p.config)
        self.assertTrue(staged_rows(p,changed,g['key'])['errors'])
        before=deepcopy(p.bank)
        self.assertFalse(approve_import(p,changed,g['key'],staged_rows(p,changed,g['key'])['revision'],'Reviewer','Original',True))
        self.assertEqual(p.bank,before)

    def test_duplicate_bank_mapping_and_partial_import_are_rejected(self):
        p=package();a=analyse_documents([document()],p.config);g=a['groups'][0]
        approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','Original',True)
        self.assertFalse(approve_account(p,a,g['key'],'1001',g['revision'],'Reviewer','Original',True))
        partial=analyse_documents([document(closing='1300.00')],p.config);g2=partial['groups'][0]
        approve_account(p,partial,g2['key'],'1000',g2['revision'],'Reviewer','Original',True)
        q=staged_rows(p,partial,g2['key']);self.assertTrue(any('do not tie' in e for e in q['errors']))
        before=deepcopy(p.config)
        self.assertFalse(approve_import(p,partial,g2['key'],q['revision'],'Reviewer','Original',True));self.assertEqual(p.bank,[]);self.assertEqual(before,p.config)


class CoverageBoundaryTests(unittest.TestCase):
    def test_extreme_date_overlap_is_an_exception_not_a_crash(self):
        config=dict(CFG,fy_start='9999-12-01',fy_end='9999-12-31')
        a=document(start='1 DEC 9999',end='31 DEC 9999')
        b=document(start='1 DEC 9999',end='31 DEC 9999',name='second.csv',opening='1200.00',closing='1400.00')
        result=analyse_documents([a,b],config)
        self.assertFalse(result['groups'][0]['coverage']['ready'])
        self.assertTrue(any('overlapping' in e for e in result['groups'][0]['errors']))
