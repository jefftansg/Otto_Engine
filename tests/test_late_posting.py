"""Synthetic month-boundary imports keep original posting dates and financial checks."""
from copy import deepcopy
from hashlib import sha256
import unittest
from engine.autofill import propose_bank_rows
from engine.bank_intake import analyse_documents,approve_account,staged_rows,approve_import
from engine.core import Package
from test_bank_intake import package
from test_ocbc_daily import source


def daily(name,**kw):
    f,doc=source(**kw)
    if name.startswith('feb'):
        doc.text_excerpt=doc.text_excerpt.replace('01 Jan 2026 To 31 Jan 2026','01 Feb 2026 To 28 Feb 2026').replace('01-Jan-2026','01-Feb-2026').replace('31-Jan-2026','28-Feb-2026')
    else:doc.text_excerpt=doc.text_excerpt.replace('31 Jan 2026 REF3','01 Feb 2026 REF3')
    payload=doc.text_excerpt.encode();doc.name=name;doc.sha256=sha256(payload).hexdigest()
    return dict(name=name,bytes=payload,sha256=doc.sha256),doc


def batch(duplicate=False):
    jan=daily('jan.pdf')
    feb=daily('feb.pdf',opening='145.00',closing='130.00' if duplicate else '145.00',debits='1 Amount 15.00' if duplicate else '0 Amount 0.00',credits='0 Amount 0.00',printed='01 Mar 2026',rows=['01 Feb 2026 REF3 SERVICE CHARGE 15.00 130.00'] if duplicate else [])
    pairs=[jan,feb];docs={f['name']:d for f,d in pairs}
    p=package();p.config.update(company_name='EXAMPLE WORKS PTE. LTD.',fy_start='2026-01-01',fy_end='2026-02-28')
    a=analyse_documents([f for f,d in pairs],p.config,lambda n,b:docs[n]);return p,a,a['groups'][0]

class LatePostingTests(unittest.TestCase):
    def test_later_month_import_preserves_dates_source_and_retries_and_zip(self):
        p,a,g=batch();self.assertEqual(g['errors'],[])
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','',True))
        proposed=staged_rows(p,a,g['key']);self.assertEqual(proposed['errors'],[])
        self.assertEqual(proposed['rows'][-1]['date'],'2026-02-01')
        self.assertTrue(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','',True))
        self.assertEqual(len(p.bank),3);self.assertEqual(p.bank[-1]['date'],'2026-02-01')
        self.assertEqual(Package.from_zip(p.to_zip()).bank,p.bank)
        self.assertFalse(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','',True))
        self.assertEqual(staged_rows(p,a,g['key'])['rows'],[])

    def test_repeated_transaction_across_monthly_exports_is_flagged_not_silently_posted(self):
        p,a,g=batch(True);self.assertEqual(g['errors'],[])
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','',True))
        before=deepcopy(p.config);proposal=staged_rows(p,a,g['key'])
        self.assertTrue(any('Possible repeated bank transaction' in e for e in proposal['errors']))
        self.assertFalse(approve_import(p,a,g['key'],proposal['revision'],'Reviewer','',True))
        self.assertEqual(p.bank,[]);self.assertEqual(p.config,before)

    def test_bad_gross_totals_or_running_balances_are_still_blocked(self):
        for change in ('20 Jan 2026 REF2 RECEIPT 70.00 161.00','20 Jan 2026 REF2 RECEIPT 71.00 160.00'):
            f,doc=daily('jan.pdf');doc.text_excerpt=doc.text_excerpt.replace('20 Jan 2026 REF2 RECEIPT 70.00 160.00',change)
            rows,errors=propose_bank_rows(doc);self.assertEqual(rows,[]);self.assertTrue(errors)

    def test_before_export_start_and_after_print_date_are_not_accepted(self):
        for value in ('31 Dec 2025 REF1','02 Feb 2026 REF1'):
            f,doc=daily('jan.pdf');doc.text_excerpt=doc.text_excerpt.replace('05 Jan 2026 REF1',value)
            rows,errors=propose_bank_rows(doc);self.assertEqual(rows,[])
            self.assertTrue(any('statement print date' in e for e in errors))

    def test_missing_or_unconfirmed_review_still_cannot_import(self):
        p,a,g=batch();before=deepcopy(p.config)
        self.assertFalse(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','',False))
        self.assertEqual(p.config,before)
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','',True))
        proposal=staged_rows(p,a,g['key'])
        self.assertFalse(approve_import(p,a,g['key'],proposal['revision'],'Reviewer','',False))
        self.assertEqual(p.bank,[])
