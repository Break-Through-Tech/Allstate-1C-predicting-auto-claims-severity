"""Behavioral safeguards for immutable splits and sealed test-target diagnostics."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

SPEC = importlib.util.spec_from_file_location('split', Path(__file__).parents[1] / 'scripts/create_partition_manifest.py')
split = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(split)


class PartitionTests(unittest.TestCase):
    def setUp(self):
        self.ids = list(range(1, 201))
        self.manifest = split.assign_partitions(self.ids)

    def test_assignment_invariant_to_input_order_and_repeat(self):
        expected = split.csv_bytes(self.manifest)
        self.assertEqual(expected, split.csv_bytes(split.assign_partitions(self.ids)))
        shuffled = np.random.default_rng(17).permutation(self.ids).tolist()
        self.assertEqual(expected, split.csv_bytes(split.assign_partitions(shuffled)))
        self.assertNotEqual(expected, split.csv_bytes(split.assign_partitions(self.ids, seed=43)))

    def test_rounding_and_nonoverlap_for_awkward_population_sizes(self):
        for n in [10, 11, 19, 101, 999, 188318]:
            with self.subTest(n=n):
                counts = split.partition_counts(n)
                self.assertEqual(sum(counts.values()), n)
                for label, weight in split.WEIGHTS.items():
                    self.assertLess(abs(counts[label] - n * weight / 100), 1)
        self.assertEqual(split.validate_manifest(self.manifest, self.ids), {'train': 150, 'validation': 30, 'test': 20})

    def test_bad_manifests_fail(self):
        duplicate = self.manifest.copy(); duplicate.loc[1, 'id'] = duplicate.loc[0, 'id']
        unknown = self.manifest.copy(); unknown.loc[0, 'id'] = 9000
        bad_label = self.manifest.copy(); bad_label.loc[0, 'partition'] = 'holdout'
        wrong_count = self.manifest.copy(); wrong_count.loc[wrong_count.partition.eq('test').idxmax(), 'partition'] = 'train'
        extra_column = self.manifest.assign(loss=100)
        for bad in [duplicate, unknown, bad_label, wrong_count, extra_column, self.manifest.iloc[1:]]:
            with self.subTest(shape=bad.shape):
                with self.assertRaises(split.IntegrityError):
                    split.validate_manifest(bad, self.ids)

    def test_duplicate_assignment_and_invalid_ids_fail(self):
        with self.assertRaises(split.IntegrityError):
            split.assign_partitions([1] * 20)
        for value in ['', '1.5', '-1', '0', 'NaN', '01', ' 1', str(2**63)]:
            with self.subTest(value=value), self.assertRaises(split.IntegrityError):
                split.canonical_id(value)

    def write_source(self, path, poison_test=False, bad_loss=None, duplicate=False):
        labels = self.manifest.set_index('id').partition.to_dict()
        with Path(path).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=split.FIELDS, lineterminator='\n')
            writer.writeheader()
            for i in self.ids:
                row = {'id': i, **dict.fromkeys(split.CATS, 'A'), **dict.fromkeys(split.CONTS, '.5'), 'loss': float(i)}
                if labels[i] == 'validation':
                    row['cat1'] = 'UNSEEN'
                if labels[i] == 'test' and poison_test:
                    row['loss'] = 'MUST_NOT_BE_PARSED'
                if i == 1 and bad_loss is not None:
                    row['loss'] = bad_loss
                if i == 2 and duplicate:
                    row['id'] = 1
                writer.writerow(row)

    def test_eligibility_all_or_abort(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.csv'
            self.write_source(path)
            ids, summary = split.check_eligibility(path, 200)
            self.assertEqual(ids, self.ids)
            self.assertEqual(summary['included_rows'], 200)
            self.assertEqual(summary['excluded_rows'], 0)
            for value in ['NaN', 'inf', '-inf', '0', '-5', 'not numeric']:
                self.write_source(path, bad_loss=value)
                with self.subTest(value=value), self.assertRaises(split.IntegrityError):
                    split.check_eligibility(path, 200)
            self.write_source(path, duplicate=True)
            with self.assertRaises(split.IntegrityError):
                split.check_eligibility(path, 200)
            self.write_source(path)
            with self.assertRaises(split.IntegrityError):
                split.check_eligibility(path, 199)

    def test_test_target_poison_does_not_reach_diagnostics(self):
        # Mandatory global eligibility is tested separately; this tests the post-split seal.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.csv'
            self.write_source(path)
            ordinary = split.load_development_rows(path, self.manifest)
            self.write_source(path, poison_test=True)
            sealed = split.load_development_rows(path, self.manifest)
            pd.testing.assert_frame_equal(ordinary, sealed)
            diagnostics, coverage = split.generate_diagnostics(self.manifest, sealed, 150, 100)
            self.assertEqual(set(diagnostics.loc[diagnostics.partition.eq('test'), 'metric']), {'row_count', 'share_of_eligible'})
            c = coverage.set_index('feature').loc['cat1']
            self.assertEqual(c.validation_unseen_level_count, 1)
            self.assertEqual(c.validation_unseen_observation_count, 30)
            self.assertEqual(c.validation_denominator, 30)
            self.assertEqual(c.validation_unseen_observation_share, 1)
            self.assertEqual(c.validation_observations_on_training_rare_levels, 0)
            self.assertEqual(len(coverage), 116)
            for label in ['train', 'validation']:
                y = sealed.loc[sealed.partition.eq(label), 'loss']
                actual = diagnostics.loc[diagnostics.partition.eq(label)].set_index('metric').value
                self.assertAlmostEqual(actual.loss_mean, y.mean())
                self.assertEqual(actual.high_loss_count, y.gt(150).sum())
            contaminated = sealed.copy(); contaminated.loc[0, 'partition'] = 'test'
            with self.assertRaises(split.IntegrityError):
                split.generate_diagnostics(self.manifest, contaminated, 150, 100)

    def test_rare_rule_boundary_and_validation_local_counts_are_separate(self):
        development = self.manifest.loc[self.manifest.partition.ne('test')].copy()
        development['loss'] = 10.0
        development = pd.concat([development, pd.DataFrame('A', index=development.index, columns=split.CATS)], axis=1)
        train_indices = development.index[development.partition.eq('train')]
        val_indices = development.index[development.partition.eq('validation')]
        development.loc[train_indices[100:], 'cat1'] = 'B'
        development.loc[val_indices[0], 'cat1'] = 'NEW'
        _, coverage = split.generate_diagnostics(self.manifest, development, 20, 100)
        row = coverage.set_index('feature').loc['cat1']
        self.assertEqual(row.training_rare_level_count, 1)  # B=50, A=100 is not rare.
        self.assertEqual(row.training_rare_observation_count, 50)
        self.assertEqual(row.validation_local_rare_level_count, 2)
        self.assertEqual(row.validation_unseen_observation_count, 1)
        self.assertEqual(row.validation_observations_on_training_rare_levels, 0)

    def test_export_never_overwrites_different_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            split.export_artifacts(tmp, {'manifest.csv': b'original'})
            split.export_artifacts(tmp, {'manifest.csv': b'original'})
            with self.assertRaises(split.IntegrityError):
                split.export_artifacts(tmp, {'new.csv': b'new', 'manifest.csv': b'changed'})
            self.assertEqual((Path(tmp) / 'manifest.csv').read_bytes(), b'original')
            self.assertFalse((Path(tmp) / 'new.csv').exists())

    def test_changed_source_hash_stops_before_reading_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); september = root / 'september'; september.mkdir()
            (root / 'source.csv').write_text('altered')
            (september / 'artifact_manifest.json').write_text(json.dumps({'source': {'path': 'source.csv', 'sha256': 'wrong'}}))
            with patch.object(split, 'ROOT', root), patch.object(split, 'SEPTEMBER', september):
                with self.assertRaisesRegex(split.IntegrityError, 'SHA-256 mismatch'):
                    split.load_and_verify_source()


if __name__ == '__main__':
    unittest.main()
