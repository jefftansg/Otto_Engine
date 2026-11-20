"""Small hand-calculated technical vectors, not professional UFS approval."""
from copy import deepcopy
from decimal import Decimal
import unittest
from engine.core import Package, generate
from engine.importers import empty_company


def package(opening='0', closing='0', **tables):
    config=empty_company()
    config.update(company_name='SYNTHETIC M0 PTE LTD',uen='DEMO-M0',
                  fy_start='2026-01-01',fy_end='2026-12-31',fy_confirmed=True,
                  bank_statement_opening=opening,bank_statement_closing=closing,bank_balances_confirmed=True)
    return Package(config,**tables)


def journal(key, date, code, debit='0', credit='0'):
    return dict(journal_id=key,date=date,account_code=code,debit=debit,credit=credit,description='Synthetic M0 vector')


class M0GoldenLedgerTests(unittest.TestCase):
    def test_first_year_director_funding_is_liability_and_financing_not_sales(self):
        p=package(closing='1000',bank=[dict(date='2026-01-02',reference='FUND-1',description='Director loan',
                                            deposit='1000',withdrawal='',account_code='2100')])
        r=generate(p)
        self.assertEqual(r['errors'],[])
        self.assertEqual((r['ledger_open'],r['ledger_end'],r['liabilities'],r['profit']),
                         (Decimal('0'),Decimal('1000'),Decimal('1000'),Decimal('0')))
        self.assertEqual(r['cashflows']['Financing'],Decimal('1000'))
        self.assertEqual(r['cashflows']['Operating'],Decimal('0'))

    def test_migrated_opening_requires_a_supported_counterpart(self):
        bank=[dict(date='2026-01-02',reference='SOFTWARE-1',description='Software',deposit='',withdrawal='100',account_code='5400')]
        opening=[journal('OPEN','2025-12-31','1000',debit='500'),journal('OPEN','2025-12-31','3100',credit='500')]
        r=generate(package(opening='500',closing='400',bank=bank,journals=opening))
        self.assertEqual(r['errors'],[])
        self.assertEqual((r['ledger_open'],r['ledger_end'],r['profit'],r['equity']),
                         (Decimal('500'),Decimal('400'),Decimal('-100'),Decimal('400')))
        self.assertEqual(r['cashflows']['Operating'],Decimal('-100'))
        unsupported=generate(package(opening='500',closing='400',bank=bank))
        self.assertTrue(any('Opening bank statement' in e for e in unsupported['errors']))
        self.assertEqual(unsupported['balances'].get('3100',Decimal('0')),Decimal('0'))

    def test_mixed_manual_cash_is_exposed_for_review_without_guessing_allocation(self):
        rows=[journal('MIX','2026-01-02','1000',debit='100'),
              journal('MIX','2026-01-02','4000',credit='60'),
              journal('MIX','2026-01-02','2100',credit='40')]
        before=deepcopy(rows)
        r=generate(package(closing='100',journals=rows))
        self.assertTrue(any('mixed classifications' in e for e in r['errors']))
        self.assertEqual(r['cashflows']['Unallocated'],Decimal('100'))
        self.assertEqual(r['cashflows']['Operating'],Decimal('0'))
        self.assertEqual(r['cashflows']['Financing'],Decimal('0'))
        self.assertEqual(rows,before)

    def test_supported_accrual_reversal_retains_both_journals_with_zero_net_result(self):
        rows=[journal('ACCRUAL','2026-01-02','5400',debit='80'),journal('ACCRUAL','2026-01-02','2200',credit='80'),
              journal('REVERSE','2026-02-02','5400',credit='80'),journal('REVERSE','2026-02-02','2200',debit='80')]
        r=generate(package(journals=rows))
        self.assertEqual(r['errors'],[])
        self.assertEqual((r['profit'],r['liabilities'],r['ledger_end']),(Decimal('0'),)*3)
        self.assertEqual({e['journal_id'] for e in r['entries']},{'ACCRUAL','REVERSE'})
        self.assertEqual(len(r['entries']),4)
        self.assertEqual(sum(r['cashflows'].values()),Decimal('0'))

    def test_after_year_end_manual_adjustment_is_rejected_without_posting(self):
        rows=[journal('LATE','2027-01-01','5400',debit='80'),journal('LATE','2027-01-01','2200',credit='80')]
        r=generate(package(journals=rows))
        self.assertEqual(len([e for e in r['errors'] if 'after financial year end' in e]),2)
        self.assertEqual(r['entries'],[])
        self.assertEqual(r['profit'],Decimal('0'))
