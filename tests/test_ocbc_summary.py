"""Synthetic OCBC layout cases; no client statement data is stored here."""
import unittest
from engine.importers import SourceDocument
from engine.autofill import extract_bank_statement


def extract(body):
    return extract_bank_statement(SourceDocument('synthetic.pdf','synthetic',[],text_excerpt=body))


class OCBCSummaryTests(unittest.TestCase):
    def test_abbreviations_and_repeated_account_heading(self):
        heading='BUSINESS GROWTH ACCOUNT 1 DEC 2024 TO 31 DEC 2024'
        b=extract('OCBC Bank\nSTATEMENT OF ACCOUNT\n'+heading+
                  '\nAccount No. 1234567890\nBALANCE B/F 1,250.00\n'+heading+
                  '\nBALANCE C/F 1,100.00')
        self.assertEqual((b['opening'],b['closing']),('1250.00','1100.00'))
        self.assertEqual((b['period_start'],b['period_end']),('2024-12-01','2024-12-31'))
        self.assertEqual(b['warnings'],[])

    def test_separate_period_line_and_spaced_lowercase_labels(self):
        b=extract('OCBC Bank\nSTATEMENT OF ACCOUNT\n1 DEC 2024 TO 31 DEC 2024\nbalance b / f 0.00\nbalance c / f 200.00')
        self.assertEqual(b['opening'],'0.00')
        self.assertEqual(b['period_end'],'2024-12-31')

    def test_conflicting_balances_are_not_chosen(self):
        b=extract('OCBC Bank\nSTATEMENT OF ACCOUNT\nBALANCE B/F 100.00\nBALANCE B/F 200.00\nBALANCE C/F 300.00')
        self.assertIsNone(b['opening'])
        self.assertTrue(any('Conflicting' in w for w in b['warnings']))

    def test_multiple_amounts_are_ambiguous(self):
        b=extract('OCBC Bank\nSTATEMENT OF ACCOUNT\nBALANCE B/F 100.00 200.00\nBALANCE C/F 200.00')
        self.assertIsNone(b['opening'])

    def test_unrelated_transaction_dates_are_not_a_period(self):
        b=extract('OCBC Bank\nSTATEMENT OF ACCOUNT\nPayment for 1 DEC 2024 TO 31 DEC 2024\nBALANCE B/F 100.00')
        self.assertIsNone(b['period_start'])

    def test_conflicting_invalid_or_non_ocbc_periods_are_not_accepted(self):
        for body in (
            'OCBC Bank\nSTATEMENT OF ACCOUNT\n1 DEC 2024 TO 31 DEC 2024\n1 JAN 2025 TO 31 JAN 2025',
            'OCBC Bank\nSTATEMENT OF ACCOUNT\n31 DEC 2024 TO 1 DEC 2024',
            'Example Bank\nSTATEMENT OF ACCOUNT\n1 DEC 2024 TO 31 DEC 2024',
        ):
            self.assertIsNone(extract(body)['period_start'])


class OCBCTransactionTests(unittest.TestCase):
    def doc(self, alteration=''):
        text='''OCBC Bank
STATEMENT OF ACCOUNT
Company Name: EXAMPLE WORKS PTE. LTD.
Account No. 1234567890
BUSINESS GROWTH ACCOUNT 1 DEC 2024 TO 31 DEC 2024
BALANCE B/F 100.00
02 DEC 02 DEC BANK CHARGES 10.00 90.00
05 DEC 05 DEC FAST TRANSFER 50.00 140.00
BALANCE C/F 140.00
Total Withdrawals/Deposits 10.00 50.00
1 JAN 2025 Promotion effective date
'''
        if alteration=='movement':text=text.replace('10.00 90.00','11.00 90.00')
        if alteration=='totals':text=text.replace('10.00 50.00','9.00 50.00')
        if alteration=='closing':text=text.replace('BALANCE C/F 140.00','BALANCE C/F 150.00')
        if alteration=='no-totals':text=text.replace('Total Withdrawals/Deposits 10.00 50.00','')
        return SourceDocument('synthetic.pdf','synthetic',[],text_excerpt=text)

    def test_running_balances_and_totals_corroborate_money_direction(self):
        from engine.autofill import propose_bank_rows
        rows,errors=propose_bank_rows(self.doc())
        self.assertEqual(errors,[])
        self.assertEqual(len(rows),2)
        self.assertEqual((rows[0]['withdrawal'],rows[1]['deposit']),('10.00','50.00'))
        self.assertTrue(all(r['account_code']=='9999' for r in rows))
        self.assertEqual(rows[0]['date'],'2024-12-02')

    def test_corrupt_or_missing_corroboration_returns_no_rows(self):
        from engine.autofill import propose_bank_rows
        for condition in ('movement','totals','closing','no-totals'):
            rows,errors=propose_bank_rows(self.doc(condition))
            self.assertEqual(rows,[])
            self.assertTrue(errors)
