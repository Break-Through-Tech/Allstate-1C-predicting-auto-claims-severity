"""Synthetic comparisons only; never modify or fit on the authoritative source."""
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from scripts.evaluation import EvaluationError, FrozenSplit, evaluate_mae
from scripts.model_comparison import (baseline_changes, gaps, stability, prediction_failures,
                                      verify_identity, score_existing, diagnostic_summaries)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.split = FrozenSplit(Path('unused'), 'a'*64, Path('unused'), 'b'*64, 'synthetic-v1',
                                 (1, 2, 3, 4), (5, 6, 7, 8), (9,), 'c'*64, 'd'*64)
        self.truth = pd.DataFrame({'id': [5, 6, 7, 8], 'loss': [1., 2., 10., 20.]})
        self.pred = pd.DataFrame({'id': [5, 6, 7, 8], 'prediction': [2., 2., 8., 10.]})
        self.evidence = evaluate_mae(self.truth, self.pred, split=self.split)

    def test_baseline_delta(self):
        self.assertEqual(baseline_changes(8, 10)[0], -2)

    def test_percentage(self):
        self.assertEqual(baseline_changes(8, 10)[1], 20)
        self.assertIsNone(baseline_changes(2, 0)[1])
        with self.assertRaises(EvaluationError):
            baseline_changes(2, np.nan)

    def test_claim_count(self):
        result = score_existing(self.truth, self.pred, self.evidence, self.split)
        self.assertEqual(result['evaluated_claim_count'], 4)

    def test_manifest_id(self):
        with self.assertRaisesRegex(EvaluationError, 'manifest_id mismatch'):
            verify_identity(dict(self.evidence, manifest_id='other'), self.split)

    def test_manifest_hash(self):
        with self.assertRaisesRegex(EvaluationError, 'manifest_sha256 mismatch'):
            verify_identity(dict(self.evidence, manifest_sha256='c'*64), self.split)

    def test_source_version(self):
        with self.assertRaisesRegex(EvaluationError, 'source_sha256 mismatch'):
            verify_identity(dict(self.evidence, source_sha256='d'*64), self.split)

    def assert_rejected(self, frame, kind):
        issues = prediction_failures(frame, self.split.validation_ids)
        self.assertIn(kind, [r[0] for r in issues])
        with self.assertRaises(EvaluationError):
            score_existing(self.truth, frame, self.evidence, self.split)

    def test_missing(self):
        self.assert_rejected(self.pred.iloc[:3], 'missing_predictions')

    def test_duplicate(self):
        self.assert_rejected(pd.concat([self.pred, self.pred.iloc[:1]]), 'duplicate_ids')

    def test_extra(self):
        self.assert_rejected(pd.concat([self.pred, pd.DataFrame({'id': [99], 'prediction': [2.]})]), 'extra_predictions')

    def test_nonfinite(self):
        for value, kind in [(np.nan, 'nan_predictions'), (np.inf, 'positive_infinity'), (-np.inf, 'negative_infinity')]:
            pred = self.pred.copy()
            pred.loc[0, 'prediction'] = value
            with self.subTest(value=value):
                self.assert_rejected(pred, kind)

    def test_nonnumeric(self):
        pred = self.pred.astype({'prediction': object})
        pred.loc[0, 'prediction'] = 'bad'
        self.assert_rejected(pred, 'non_numeric_predictions')

    def test_null_id(self):
        pred = self.pred.astype({'id': object})
        pred.loc[0, 'id'] = None
        self.assert_rejected(pred, 'null_ids')

    def test_empty(self):
        self.assert_rejected(self.pred.iloc[:0], 'empty_artifact')

    def test_wrong_scale(self):
        with self.assertRaisesRegex(EvaluationError, 'scale'):
            verify_identity(dict(self.evidence, units='log1p(loss)'), self.split)

    def test_recorded_mae_mismatch(self):
        with self.assertRaisesRegex(EvaluationError, 'disagree'):
            score_existing(self.truth, self.pred, dict(self.evidence, mae=99), self.split)

    def test_error_bin_support(self):
        bins, _, _ = diagnostic_summaries(self.truth, self.pred, [1., 2., 3., 4.])
        self.assertEqual(len(bins), 7)
        self.assertEqual([b['claim_count'] for b in bins], [1, 1, 0, 0, 0, 0, 2])
        self.assertEqual(sum(b['claim_count'] for b in bins), 4)
        self.assertEqual(sum(b['validation_share'] for b in bins), 1)

    def test_tied_quantiles_and_outside_training_range(self):
        bins, tails, _ = diagnostic_summaries(self.truth, self.pred, [2., 2., 2., 2.])
        self.assertEqual(sum(b['claim_count'] for b in bins), 4)
        self.assertEqual(tails[0]['claim_count'], 2)

    def test_high_loss_mae(self):
        _, tails, _ = diagnostic_summaries(self.truth, self.pred, [1., 2., 3., 4.])
        self.assertEqual(tails[0]['claim_count'], 2)
        self.assertEqual(tails[0]['mae'], 6)
        self.assertEqual(tails[0]['validation_denominator'], 4)

    def test_signed_error(self):
        bins, tails, _ = diagnostic_summaries(self.truth, self.pred, [1., 2., 3., 4.])
        self.assertEqual(tails[0]['mean_signed_error'], -6)
        self.assertEqual(bins[0]['mean_signed_error'], 1)

    def test_generalization_gap(self):
        result = gaps(10, 6, 9)
        self.assertEqual(result['generalization_gap'], 4)
        self.assertEqual(result['validation_minus_cv_mean'], 1)

    def test_unavailable_metrics(self):
        result = gaps(10)
        self.assertIsNone(result['generalization_gap'])
        self.assertIsNone(result['validation_minus_cv_mean'])

    def test_unavailable_stability(self):
        for values in [None, [1.]]:
            self.assertTrue(stability(values)['status'].startswith('NOT_ASSESSED'))

    def test_fold_stability(self):
        result = stability([1., 2., 3.])
        self.assertEqual(result['std_mae'], 1)
        self.assertEqual(result['range_mae'], 2)
        self.assertEqual(result['count'], 3)

    def test_reproducible(self):
        a = score_existing(self.truth, self.pred, self.evidence, self.split)
        b = score_existing(self.truth.iloc[::-1], self.pred.iloc[::-1], self.evidence, self.split)
        self.assertEqual(a, b)
        self.assertEqual(diagnostic_summaries(self.truth, self.pred, [1., 2., 3., 4.]),
                         diagnostic_summaries(self.truth.iloc[::-1], self.pred.iloc[::-1], [4., 3., 2., 1.]))

    def test_canonical_string_ids_in_diagnostics(self):
        self.assertEqual(diagnostic_summaries(self.truth, self.pred, [1., 2., 3., 4.]),
                         diagnostic_summaries(self.truth, self.pred.astype({'id': 'string'}), [1., 2., 3., 4.]))

    def test_valid_predictions_have_no_failures(self):
        self.assertEqual(prediction_failures(self.pred, self.split.validation_ids), [])


if __name__ == '__main__':
    unittest.main()
