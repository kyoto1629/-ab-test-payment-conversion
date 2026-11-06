"""Регрессия исходного анализа и проверки важных контрактов данных."""
import json
from pathlib import Path
import sys
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ab_test.data import load_data, prepare_data
from ab_test.metrics import aggregate_users
from ab_test.pipeline import analyze
from ab_test.statistics import cluster_test


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users, cls.payments = load_data()
        cls.result = analyze()
        cls.baseline = json.loads((ROOT / 'tests/baseline_original.json').read_text())

    def test_original_statistics_preserved(self):
        for key, expected in self.baseline.items():
            if key == 'funnel':
                continue
            with self.subTest(key=key):
                tolerance = 1e-6 if key.startswith('ci_') else 1e-12
                self.assertAlmostEqual(self.result['statistics'][key], expected, delta=tolerance)

    def test_original_funnel_preserved(self):
        self.assertEqual(self.result['funnel'].to_dict(), self.baseline['funnel'])

    def test_duplicate_user_rejected(self):
        with self.assertRaisesRegex(ValueError, 'user_id'):
            prepare_data(pd.concat([self.users, self.users.iloc[:1]]), self.payments)

    def test_duplicate_payment_rejected(self):
        with self.assertRaisesRegex(ValueError, 'payment_id'):
            prepare_data(self.users, pd.concat([self.payments, self.payments.iloc[:1]]))

    def test_assigned_group_is_authoritative(self):
        users, payments, _ = prepare_data(self.users, self.payments)
        expected = payments['user_id'].map(users.set_index('user_id')['group'])
        self.assertTrue(payments['group'].eq(expected).all())
        self.assertTrue(payments['user_id'].isin(users['user_id']).all())

    def test_out_of_order_event_rejected(self):
        payments = self.payments.copy()
        idx = payments.loc[payments['user_id'].isin(self.result['users']['user_id']) & payments['step2_entered'].notna()].index[0]
        payments.loc[idx, 'step2_entered'] = payments.loc[idx, 'step1_opened'] - pd.Timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError, 'последовательность'):
            prepare_data(self.users, payments)

    def test_users_without_attempts_kept(self):
        users = pd.DataFrame({'user_id': [1,2,3], 'group': ['A','A','B']})
        payments = pd.DataFrame({'user_id': [1,1], 'payment_id': [10,11], 'success': [0,1]})
        result = aggregate_users(users, payments).set_index('user_id')
        self.assertEqual(result.loc[1, 'attempts'], 2)
        self.assertEqual(result.loc[2, 'attempts'], 0)
        self.assertEqual(result.loc[3, 'successes'], 0)

    def test_attempt_without_opening_rejected(self):
        payments = self.payments.copy()
        idx = payments.loc[payments['user_id'].isin(self.result['users']['user_id'])].index[0]
        payments.loc[idx, ['step1_opened', 'step2_entered', 'step3_confirmed', 'step4_success']] = pd.NaT
        with self.assertRaisesRegex(ValueError, 'открытия формы'):
            prepare_data(self.users, payments)

    def test_alpha_controls_ci(self):
        stats = self.result['user_stats']
        a = cluster_test(stats, alpha=0.05)
        b = cluster_test(stats, alpha=0.01)
        self.assertLess(b['ci_lower'], a['ci_lower'])
        self.assertGreater(b['ci_upper'], a['ci_upper'])

    def test_insufficient_data_rejected(self):
        sample = pd.DataFrame({'group':['A','B'], 'attempts':[1,1], 'successes':[0,1]})
        with self.assertRaisesRegex(ValueError, 'минимум два'):
            cluster_test(sample)


if __name__ == '__main__':
    unittest.main()
