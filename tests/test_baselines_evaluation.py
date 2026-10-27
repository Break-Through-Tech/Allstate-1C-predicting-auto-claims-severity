import dataclasses
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from scripts.evaluation import FrozenSplit, EvaluationError, evaluate_mae, load_partition_targets
from scripts.run_baselines import fit_constants, predict_constant


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.split = FrozenSplit(Path('unused'), 'a'*64, Path('unused'), 'b'*64, 'synthetic-v1',
                                 (1, 2, 3, 4), (5, 6, 7), (8,), 'c'*64, 'd'*64)
        self.truth = pd.DataFrame({'id': [5, 6, 7], 'loss': [10., 20., 30.]})
        self.pred = pd.DataFrame({'id': [5, 6, 7], 'prediction': [8., 22., 30.]})
        self.train = pd.DataFrame({'id': [1, 2, 3, 4], 'loss': [1., 2., 3., 100.]})

    def score(self, pred=None, truth=None):
        return evaluate_mae(self.truth if truth is None else truth, self.pred if pred is None else pred, split=self.split)

    def test_known_mae_and_count(self):
        result = self.score()
        self.assertAlmostEqual(result['mae'], 4/3)
        self.assertEqual(result['evaluated_claim_count'], 3)
        self.assertEqual(result['partition_id'], 'synthetic-v1:validation')

    def test_shuffled_rows(self):
        self.assertEqual(self.score()['mae'], self.score(self.pred.iloc[[2, 0, 1]])['mae'])

    def test_bad_coverage(self):
        for frame in [self.pred.iloc[:2], pd.concat([self.pred, self.pred.iloc[:1]]),
                      pd.concat([self.pred, pd.DataFrame({'id': [9], 'prediction': [1.]})]), self.pred.iloc[:0]]:
            with self.subTest(frame=frame), self.assertRaises(EvaluationError):
                self.score(frame)

    def test_duplicate_truth(self):
        with self.assertRaises(EvaluationError):
            self.score(truth=pd.concat([self.truth, self.truth.iloc[:1]]))

    def test_invalid_predictions(self):
        for value in [np.nan, np.inf, -np.inf, 'bad', '2', None, True]:
            pred = self.pred.astype({'prediction': object})
            pred.loc[0, 'prediction'] = value
            if isinstance(value, float):
                pred.prediction = pred.prediction.astype(float)
            with self.subTest(value=value), self.assertRaises(EvaluationError):
                self.score(pred)

    def test_invalid_truth(self):
        for value in [np.nan, np.inf, -np.inf, 'bad', 0, -1]:
            truth = self.truth.copy().astype({'loss': object})
            truth.loc[0, 'loss'] = value
            if not isinstance(value, str):
                truth.loss = truth.loss.astype(float)
            with self.subTest(value=value), self.assertRaises(EvaluationError):
                self.score(truth=truth)

    def test_invalid_ids(self):
        for value in [None, True, 0, -1, 5.5, '05', 'bad']:
            pred = self.pred.astype({'id': object})
            pred.loc[0, 'id'] = value
            with self.subTest(value=value), self.assertRaises(EvaluationError):
                self.score(pred)

    def test_training_only_and_reproduction(self):
        constants = fit_constants(self.train, self.split)
        self.assertEqual(constants, {'mean': 26.5, 'median': 2.5})
        for name, value in constants.items():
            pred = predict_constant(value, self.split)
            self.assertEqual(set(pred.id), set(self.split.validation_ids))
            self.assertTrue(pred.prediction.eq(value).all())
            again = fit_constants(self.train.iloc[::-1], self.split)
            self.assertEqual(self.score(pred)['mae'], self.score(predict_constant(again[name], self.split))['mae'])
        self.truth.loss *= 1000
        self.assertEqual(constants, fit_constants(self.train, self.split))

    def test_validation_cannot_enter_training(self):
        with self.assertRaises(EvaluationError):
            fit_constants(pd.concat([self.train, self.truth]), self.split)

    def test_partition_overlap(self):
        with self.assertRaises(EvaluationError):
            dataclasses.replace(self.split, validation_ids=(4, 5, 6)).validate()

    def test_bad_truth_coverage_and_schema(self):
        for truth in [self.truth.iloc[:0], self.truth.iloc[:2], self.truth.assign(extra=1),
                      self.truth.assign(id=[5, 6, 8])]:
            with self.subTest(truth=truth), self.assertRaises(EvaluationError):
                self.score(truth=truth)

    def test_bool_complex_and_wrong_prediction_schema(self):
        for pred in [self.pred.assign(prediction=True), self.pred.assign(prediction=1+2j),
                     self.pred.rename(columns={'prediction': 'wrong'})]:
            with self.subTest(pred=pred), self.assertRaises(EvaluationError):
                self.score(pred)

    def test_test_loss_never_converted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.csv'
            path.write_text('id,loss\n1,1\n2,2\n3,3\n4,100\n5,10\n6,20\n7,30\n8,DO_NOT_PARSE_TEST_TARGET\n')
            training, validation = load_partition_targets(dataclasses.replace(self.split, source_path=path))
            pd.testing.assert_frame_equal(training, self.train)
            pd.testing.assert_frame_equal(validation, self.truth)


if __name__ == '__main__':
    unittest.main()
