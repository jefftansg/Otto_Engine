"""No ACRA/profile input: statement owner must never come from a counterparty."""
from hashlib import sha256
from copy import deepcopy
import unittest
from engine.importers import SourceDocument,SourceTable,empty_company
from engine.auto import analyse,company_name
from engine.bank_intake import identify
from engine.bank_headers import account_holder,header_lines


def bank(name='account.pdf',owner='EXAMPLE TRADING PTE. LTD.',counterparty='ANOTHER SUPPLIER PTE. LTD.'):
    text=('Daily Statement of Account - Details\nFrom 01 May 2026 To 31 May 2026\n'
          'Account Number 1234567890 - SGD Opening Balance 100.00 01-May-2026\n'
          'Account Name '+owner+' Ledger Balance 150.00 31-May-2026\n'
          'Debits 0 Amount 0.00 Available Balance 150.00\nCredits 1 Amount 50.00 Total Hold Amount 0.00\n'
          'BIC Code OCBCSGSGXXX\nBIC Name OVERSEA-CHINESE BANKING CORPORATION LIMITED\n'
          'Post Date Bank Ref. Client Ref. Debit Amount Credit Amount Balance\n'
          '31 May 2026 BANKREF 50.00 150.00\n31 May 2026 TRANSFER\nFund Transfer from\n'+counterparty+'\n'
          'Printed On 01 Jun 2026 12:00:00')
    payload=text.encode();item=dict(name=name,bytes=payload,sha256=sha256(payload).hexdigest())
    return item,SourceDocument(name,item['sha256'],[],text)


class BankHeaderIdentityTests(unittest.TestCase):
    def test_inline_owner_does_not_include_ledger_field_or_counterparty(self):
        item,doc=bank()
        self.assertEqual(company_name(doc),'EXAMPLE TRADING PTE. LTD.')
        self.assertEqual(identify(doc)['company'],'EXAMPLE TRADING PTE. LTD.')
        self.assertNotIn('150.00',account_holder(doc)['value'])

    def test_bank_only_sources_propose_owner_but_no_uen_or_acra_profile(self):
        one,doc=bank();two,doc2=bank('other.pdf',counterparty='DIFFERENT CUSTOMER PTE. LTD.')
        mapping={doc.name:doc,doc2.name:doc2};cfg=empty_company();before=deepcopy(cfg)
        a=analyse([one,two],cfg,lambda name,data:mapping[name])
        self.assertEqual(a['proposals']['company_name']['value'],'EXAMPLE TRADING PTE. LTD.')
        self.assertEqual(a['conflicts'],[]);self.assertNotIn('uen',a['proposals'])
        self.assertTrue(all(r['type']=='Bank statement' for r in a['inventory']))
        self.assertEqual(cfg,before)

    def test_missing_owner_stays_unknown_not_the_transfer_party(self):
        item,doc=bank();doc.text_excerpt=doc.text_excerpt.replace('Account Name EXAMPLE TRADING PTE. LTD. Ledger Balance 150.00 31-May-2026','Ledger Balance 150.00 31-May-2026')
        self.assertEqual(company_name(doc),'')
        self.assertEqual(identify(doc)['company'],'')
        doc.text_excerpt='OCBC Bank\nSTATEMENT OF ACCOUNT\n2026-01-01 transfer\nANOTHER SUPPLIER PTE. LTD.'
        self.assertEqual(company_name(doc),'')

    def test_conflicting_header_owners_are_not_resolved_by_first_match(self):
        item,doc=bank();doc.text_excerpt=doc.text_excerpt.replace('Post Date Bank Ref.','Account Holder: OTHER COMPANY PTE LTD\nPost Date Bank Ref.')
        self.assertEqual(company_name(doc),'')
        self.assertTrue(any('Conflicting account-holder' in e for e in identify(doc)['errors']))

    def test_legacy_company_heading_and_labelled_csv_remain_supported(self):
        item,doc=bank();doc.text_excerpt='OCBC Bank\nSTATEMENT OF ACCOUNT\nEXAMPLE TRADING PTE. LTD.\nTransaction Value\nDate Date Description\nANOTHER SUPPLIER PTE. LTD.'
        self.assertEqual(company_name(doc),'EXAMPLE TRADING PTE. LTD.')
        doc.text_excerpt=doc.text_excerpt.replace('Transaction Value','1 JAN 2026 TO 31 JAN 2026\nTransaction Value')
        self.assertIn('1 JAN 2026 TO 31 JAN 2026',header_lines(doc))
        doc=SourceDocument('bank.csv','hash',[SourceTable('CSV',[['Company Name','EXAMPLE TRADING PTE. LTD.'],['Date','Description'],['2026-01-01','ANOTHER SUPPLIER PTE. LTD.']])])
        self.assertEqual(company_name(doc),'EXAMPLE TRADING PTE. LTD.')
