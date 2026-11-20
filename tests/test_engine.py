import copy
import unittest
from pathlib import Path
from engine.core import Package, generate, money
from engine.reports import management_pdf, financial_statements_pdf, xlsx_report

BASE=Path(__file__).resolve().parents[1]/'sample_company'

class EngineTests(unittest.TestCase):
    def setUp(self):self.p=Package.from_directory(BASE)

    def test_bank_payment_mapped_to_depreciation_requires_review(self):
        package = Package.from_directory(BASE)
        package.bank.append({
            "date": package.config["fy_end"],
            "description": "Fictional payment mapped to depreciation",
            "reference": "CASHFLOW-TEST-01",
            "deposit": "0",
            "withdrawal": "20.00",
            "account_code": "5700",
        })
        package.config["bank_statement_closing"] = "1748.00"

        result = generate(package)
        cashflows = result["cashflows"]
        visible_movement = sum(
            cashflows[category]
            for category in ("Operating", "Investing", "Financing", "Unallocated")
        )

        with self.subTest("validation flags the incorrect mapping"):
            self.assertTrue(
                any("noncash" in message.lower() for message in result["errors"]),
                result["errors"],
            )
        with self.subTest("draft shows the payment for review"):
            self.assertEqual(cashflows["Unallocated"], -20)
            self.assertEqual(
                visible_movement, result["ledger_end"] - result["ledger_open"]
            )

    def test_bank_and_manual_journal_id_collision_is_flagged(self):
        package = Package.from_directory(BASE)
        journal = {
            "journal_id": "BANK-0001",
            "date": package.config["fy_end"],
            "description": "Fictional manual adjustment",
        }
        package.journals.extend([
            {**journal, "account_code": "5600", "debit": "10.00", "credit": "0"},
            {**journal, "account_code": "2200", "debit": "0", "credit": "10.00"},
        ])

        result = generate(package)

        self.assertTrue(
            any(
                "BANK-0001" in message and "collision" in message.lower()
                for message in result["errors"]
            ),
            result["errors"],
        )

    def test_demo_balances(self):
        r=generate(self.p)
        self.assertEqual(r['errors'],[])
        self.assertEqual(r['revenue'],money('1500'))
        self.assertEqual(r['expenses'],money('482'))
        self.assertEqual(r['profit'],money('1018'))
        self.assertEqual(r['assets'],money('1768'))
        self.assertEqual(r['liabilities'],money('650'))
        self.assertEqual(r['equity'],money('1118'))
        self.assertEqual(r['bank_close'],r['ledger_end'])
        self.assertEqual(r['trial_debit'],r['trial_credit'])

    def test_unclassified_blocks(self):
        self.p.bank[0]['account_code']='9999'
        self.assertTrue(any('unresolved classification' in e for e in generate(self.p)['errors']))

    def test_duplicate_reference_blocks(self):
        self.p.bank[1]['reference']=self.p.bank[0]['reference']
        self.assertTrue(any('Duplicate bank reference' in e for e in generate(self.p)['errors']))

    def test_unbalanced_journal_blocks(self):
        self.p.journals[1]['credit']='90'
        self.assertTrue(any('unbalanced' in e for e in generate(self.p)['errors']))

    def test_bank_reconciliation_blocks(self):
        self.p.config['bank_statement_closing']='9999'
        self.assertTrue(any('Closing bank statement' in e for e in generate(self.p)['errors']))

    def test_receivables_control(self):
        self.p.invoices=[dict(invoice_no='INV-99',date='2026-06-01',due_date='2026-06-30',customer='A',amount='500',amount_paid='0')]
        self.assertTrue(any('AR invoice schedule' in e for e in generate(self.p)['errors']))

    def test_package_roundtrip(self):
        p=Package.from_zip(self.p.to_zip())
        self.assertEqual(p.bank,self.p.bank)
        self.assertEqual(generate(p)['profit'],money('1018'))

    def test_pdf_excel_signatures(self):
        r=generate(self.p)
        self.assertTrue(management_pdf(r).startswith(b'%PDF-'))
        self.assertTrue(financial_statements_pdf(r).startswith(b'%PDF-'))
        self.assertTrue(xlsx_report(r).startswith(b'PK'))

if __name__=='__main__':unittest.main()
