"""Synthetic daily-details export regressions: source identity, totals and cutoffs."""
from copy import deepcopy
from hashlib import sha256
import unittest
from engine.importers import SourceDocument,empty_company
from engine.autofill import extract_bank_statement,propose_bank_rows
from engine.bank_intake import identify,analyse_documents
from engine.auto import analyse


def source(opening='100.00',closing='145.00',debits='2 Amount 25.00',credits='1 Amount 70.00',printed='01 Feb 2026',rows=None):
    if rows is None:rows=['31 Jan 2026 REF3 SERVICE CHARGE 15.00 145.00','31 Jan 2026 CHARGES',
                        '20 Jan 2026 REF2 RECEIPT 70.00 160.00','20 Jan 2026 TRANSFER','OTHER SUPPLIER PTE. LTD.',
                        '05 Jan 2026 REF1 CHARGES 10.00 90.00','05 Jan 2026 CHARGES']
    lines=['Daily Statement of Account - Details','From 01 Jan 2026 To 31 Jan 2026',
           'Account Number 1234567890 - SGD Opening Balance '+opening+' 01-Jan-2026',
           'Account Name EXAMPLE WORKS PTE. LTD. Ledger Balance '+closing+' 31-Jan-2026',
           'Debits '+debits+' Available Balance '+closing,'Credits '+credits+' Total Hold Amount 0.00',
           'BIC Code OCBCSGSGXXX BIC Name OVERSEA-CHINESE BANKING CORPORATION','LIMITED',
           'Post Date Bank Ref. Client Ref. Debit Amount Credit Amount Balance','Value Date Transaction Desc.','Details']+rows
    if printed:lines+=['Printed On '+printed+' 12:30:00']
    text='\n'.join(lines);payload=text.encode();doc=SourceDocument('daily.pdf',sha256(payload).hexdigest(),[],text)
    return dict(name=doc.name,sha256=doc.sha256,bytes=payload),doc


class OcbcDailyTests(unittest.TestCase):
    def test_header_owner_bank_currency_and_checked_ledger_balance(self):
        item,doc=source();summary=extract_bank_statement(doc);row=identify(doc)
        self.assertEqual(summary['closing'],'145.00');self.assertEqual(summary['warnings'],[])
        self.assertEqual((row['bank'],row['company'],row['currency']),('OCBC','EXAMPLE WORKS PTE. LTD.','SGD'))
        self.assertEqual(row['errors'],[]);self.assertEqual(summary['period_end'],'2026-01-31')

    def test_no_acra_and_no_uen_or_counterparty_company_inference(self):
        item,doc=source();cfg=empty_company();a=analyse([item],cfg,lambda n,b:doc)
        self.assertEqual(a['proposals']['company_name']['value'],'EXAMPLE WORKS PTE. LTD.')
        self.assertNotIn('uen',a['proposals']);self.assertEqual(a['conflicts'],[])

    def test_ledger_label_is_not_a_global_closing_balance_alias(self):
        item,doc=source();doc.text_excerpt=doc.text_excerpt.replace('Daily Statement of Account - Details','Account Statement')
        self.assertIsNone(extract_bank_statement(doc)['closing'])

    def test_bad_summary_arithmetic_does_not_become_a_closing_balance(self):
        item,doc=source(closing='146.00');r=extract_bank_statement(doc)
        self.assertIsNone(r['closing']);self.assertTrue(any('differs' in e for e in r['warnings']))
        self.assertTrue(propose_bank_rows(doc)[1])

    def test_conflicting_ledger_fields_fail_closed(self):
        item,doc=source();doc.text_excerpt=doc.text_excerpt.replace('BIC Code','Ledger Balance 999.00\nBIC Code')
        self.assertIsNone(extract_bank_statement(doc)['closing']);self.assertTrue(identify(doc)['errors'])

    def test_missing_print_date_cannot_prove_completed_coverage(self):
        item,doc=source(printed='');summary=extract_bank_statement(doc)
        self.assertIsNone(summary['period_end']);self.assertTrue(summary['warnings'])
        self.assertTrue(identify(doc)['errors'])

    def test_printed_before_requested_end_is_partial_not_a_full_month(self):
        item,doc=source(printed='27 Jan 2026');summary=extract_bank_statement(doc)
        self.assertEqual(summary['period_end'],'2026-01-27');self.assertEqual(summary['requested_period_end'],'2026-01-31')
        cfg=dict(empty_company(),fy_start='2026-01-01',fy_end='2026-01-31')
        a=analyse_documents([item],cfg,lambda n,b:doc)
        self.assertFalse(a['groups'][0]['coverage']['ready'])
        self.assertEqual(a['groups'][0]['coverage']['months'][0]['status'],'Missing / incomplete')
        self.assertTrue(propose_bank_rows(doc)[1])

    def test_descending_transactions_reconcile_counts_gross_totals_and_running_balances(self):
        item,doc=source();rows,errors=propose_bank_rows(doc)
        self.assertEqual(errors,[]);self.assertEqual(len(rows),3)
        self.assertEqual([r['date'] for r in rows],['2026-01-05','2026-01-20','2026-01-31'])
        self.assertEqual([r['deposit'] for r in rows],['','70.00',''])
        self.assertEqual([r['withdrawal'] for r in rows],['10.00','','15.00'])
        self.assertTrue(all(r['account_code']=='9999' for r in rows))
        self.assertIn('OTHER SUPPLIER PTE. LTD.',rows[1]['description'])
        self.assertEqual(rows[1]['source_reference'],'REF2 RECEIPT')

    def test_zero_activity_is_valid_not_a_missing_table(self):
        item,doc=source(opening='0.00',closing='0.00',debits='0 Amount 0.00',credits='0 Amount 0.00',rows=[])
        self.assertEqual(propose_bank_rows(doc),([],[]));self.assertEqual(identify(doc)['errors'],[])

    def test_omitted_transaction_cannot_pass_just_because_summary_totals_tie(self):
        item,doc=source();doc.text_excerpt=doc.text_excerpt.replace('20 Jan 2026 REF2 RECEIPT 70.00 160.00','')
        self.assertEqual(propose_bank_rows(doc)[0],[]);self.assertTrue(propose_bank_rows(doc)[1])

    def test_post_date_value_date_cutoff_needs_review_not_automatic_backdating(self):
        item,doc=source();doc.text_excerpt=doc.text_excerpt.replace('31 Jan 2026 REF3','01 Feb 2026 REF3')
        rows,errors=propose_bank_rows(doc);self.assertEqual(rows,[])
        self.assertTrue(any('posting/value-date' in e for e in errors))

    def test_overdraft_notation_and_bad_running_balances_are_not_guessed(self):
        for change in ('145.00 31-Jan-2026','REF2 RECEIPT 70.00 160.00'):
            item,doc=source()
            doc.text_excerpt=doc.text_excerpt.replace(change,change+' DR' if change.startswith('145') else 'REF2 RECEIPT 70.00 161.00')
            self.assertEqual(propose_bank_rows(doc)[0],[]);self.assertTrue(propose_bank_rows(doc)[1])
