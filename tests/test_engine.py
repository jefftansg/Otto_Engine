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

    def test_missing_bank_opening_balance_requires_review(self):
        for opening in ("", None):
            with self.subTest(opening=opening):
                package = Package.from_directory(BASE)
                if opening is None:
                    package.config.pop("bank_statement_opening")
                else:
                    package.config["bank_statement_opening"] = opening

                result = generate(package)

                self.assertIn(
                    "Bank statement opening balance is required.",
                    result["errors"],
                )

        package = Package.from_directory(BASE)
        package.config["bank_statement_opening"] = "0.00"
        self.assertEqual(generate(package)["errors"], [])

    def test_missing_bank_closing_balance_requires_review(self):
        sample = Package.from_directory(BASE)
        config = {**sample.config, "bank_statement_opening": "0.00"}
        config.pop("bank_statement_closing", None)

        cases = (
            ("missing", config),
            ("blank", {**config, "bank_statement_closing": ""}),
        )
        for label, case in cases:
            with self.subTest(closing=label):
                self.assertIn(
                    "Bank statement closing balance is required.",
                    generate(Package(case))["errors"],
                )

        explicit_zero = {**config, "bank_statement_closing": "0.00"}
        self.assertEqual(generate(Package(explicit_zero))["errors"], [])

    def test_manual_cash_journal_mapped_to_depreciation_requires_review(self):
        package = Package.from_directory(BASE)
        for journal_id, account, debit, credit in (
            ("TEST-MANUAL-OUT", "5700", "20.00", "0"),
            ("TEST-MANUAL-IN", "4000", "0", "20.00"),
        ):
            journal = {
                "journal_id": journal_id,
                "date": package.config["fy_end"],
                "description": "Fictional cash-flow test",
            }
            package.journals.extend([
                {**journal, "account_code": account, "debit": debit, "credit": credit},
                {**journal, "account_code": "1000", "debit": credit, "credit": debit},
            ])

        result = generate(package)
        cashflows = result["cashflows"]
        visible = sum(
            cashflows[category]
            for category in ("Operating", "Investing", "Financing", "Unallocated")
        )

        with self.subTest("validation identifies the manual journal"):
            self.assertTrue(
                any(
                    "TEST-MANUAL-OUT" in error and "noncash" in error.lower()
                    for error in result["errors"]
                ),
                result["errors"],
            )
        with self.subTest("withdrawal is visible for review"):
            self.assertEqual(cashflows["Unallocated"], -20)
        with self.subTest("visible cash movement agrees with the ledger"):
            self.assertEqual(visible, result["ledger_end"] - result["ledger_open"])

    def test_bank_workpapers_distinguish_missing_balances_from_zero(self):
        from io import BytesIO

        from openpyxl import load_workbook

        from engine.reports import xlsx_report

        cases = (
            ("", "0.00", "Not provided", 0, "=B4-B5"),
            ("0.00", "", 0, "Not provided", None),
            ("0.00", "0.00", 0, 0, "=B4-B5"),
        )
        for opening, closing, expected_opening, expected_closing, expected_difference in cases:
            with self.subTest(opening=opening, closing=closing):
                package = Package.from_directory(BASE)
                package.config["bank_statement_opening"] = opening
                package.config["bank_statement_closing"] = closing

                with BytesIO(xlsx_report(generate(package))) as output:
                    workbook = load_workbook(output, data_only=False)
                    try:
                        sheet = workbook["Bank Reconciliation"]
                        self.assertEqual(
                            (sheet["B2"].value, sheet["B4"].value, sheet["B6"].value),
                            (expected_opening, expected_closing, expected_difference),
                        )
                    finally:
                        workbook.close()

    def test_draft_pdfs_distinguish_missing_bank_balances_from_zero(self):
        from io import BytesIO

        import pdfplumber

        from engine.reports import financial_statements_pdf, management_pdf

        def pdf_text(content):
            with pdfplumber.open(BytesIO(content)) as pdf:
                return " ".join(
                    " ".join(page.extract_text() or "" for page in pdf.pages).split()
                )

        sample = Package.from_directory(BASE)
        for supplied, balance, calculation in (
            ("", "Not provided", "Not available"),
            ("0.00", "0.00", "0.00"),
        ):
            config = {
                **sample.config,
                "bank_statement_opening": supplied,
                "bank_statement_closing": supplied,
            }
            result = generate(Package(config))
            management = pdf_text(management_pdf(result))
            financial = pdf_text(financial_statements_pdf(result))

            with self.subTest(balance=supplied, report="management accounts"):
                for label, value in (
                    ("Statement beginning balance", balance),
                    ("Expected bank statement closing", calculation),
                    ("Statement closing balance entered", balance),
                    ("Statement minus ledger difference", calculation),
                ):
                    self.assertIn(f"{label} {value}", management)

            with self.subTest(balance=supplied, report="financial statements"):
                closing = "SGD 0.00" if supplied else "not provided"
                self.assertIn(f"Bank statement closing input is {closing}.", financial)

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
