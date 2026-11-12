"""Isolation, metric and workflow safeguards; no real candidate training."""
import json
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts.evaluation import EvaluationError, FrozenSplit, evaluate_mae, evaluate_training_mae
from scripts import run_xgboost as runner


def split(source=Path('not-opened.csv')):
    return FrozenSplit(source, '0'*64, Path('not-opened-manifest.csv'), '1'*64,
                       'unit-split', tuple(range(1, 11)), (11,), (12,), '2'*64, '3'*64)


def result(candidate_id='A2-C01', mae=20., depth=3, trees=300, rate=.05, runtime=5.):
    return {'id': candidate_id, 'status': 'PASS', 'pooled_oof_mae': mae,
            'runtime_seconds': runtime, 'parameters': {'max_depth': depth, 'n_estimators': trees,
                                                     'learning_rate': rate}}


def receipt():
    return {'stage': 'INITIAL_COMPLETE', 'initial_winner': 'A2-C01',
            'results': [result()], 'releases': {}, 'cv_fits_attempted': 0,
            'configurations_attempted': 0, 'fit_runtime_seconds': 0,
            'readiness': {'release_sequence': 'amend_to_one_release',
                          'minimum_mae_improvement': 1., 'deadline_utc': '2099-01-01T00:00:00+00:00',
                          'max_runtime_seconds': 120}}


def campaign(output, stage='FOLLOWUP_FROZEN'):
    """Ledger-only fixture; never authorizes or opens the real source."""
    config = json.loads((runner.ROOT / runner.CONFIG).read_text())
    environment = runner.actual_environment()
    rec = receipt()
    rec.update(stage=stage, synthetic=False, config_sha256=runner.sha256(runner.ROOT / runner.CONFIG),
               code_sha256=runner.code_hashes(), configurations_attempted=5, cv_fits_attempted=25,
               environment=environment, python=environment['python'], versions=deepcopy(environment['packages']),
               frozen_inputs={'source_sha256': config['inputs']['source_sha256'],
                              'manifest_sha256': config['inputs']['manifest_sha256'],
                              'cv_folds_sha256': config['inputs']['cv_folds_sha256'],
                              'training_claims': config['evaluation']['training_claims']})
    rec['results'] = [dict(result(c['id']), parameters=runner.model_params(config, c),
                           fold_results=[{'fold': i, 'claims': 1, 'mae': 1.} for i in range(5)])
                      for c in config['initial_candidates']]
    if stage in {'FOLLOWUP_COMPLETE', 'COMPLETE'}:
        rec['results'].append(dict(deepcopy(rec['results'][0]), id='A2-C06'))
        rec.update(configurations_attempted=6, cv_fits_attempted=30)
    if stage == 'COMPLETE':
        rec['releases']['final'] = {'status': 'PASS'}
    if stage != 'INITIAL_COMPLETE':
        runner.write_json(output / 'followup_plan.json', {'note': 'ledger-only fixture'})
        rec['followup_plan_sha256'] = runner.sha256(output / 'followup_plan.json')
    return rec


class RunnerTests(unittest.TestCase):
    def test_shared_training_metric_and_negative_prediction(self):
        truth = pd.DataFrame({'id': [2, 1], 'loss': [10., 2.]})
        pred = pd.DataFrame({'id': [1, 2], 'prediction': [-2., 8.]})
        score = evaluate_training_mae(truth, pred, split=split(), held_out_ids=[1, 2])
        self.assertEqual(score['mae'], 3.)
        self.assertEqual(score['partition'], 'training_oof')
        self.assertTrue(all(score['checks'].values()))

    def test_training_metric_rejects_validation_test_duplicates_and_nonfinite(self):
        truth = pd.DataFrame({'id': [1, 2], 'loss': [2., 10.]})
        pred = pd.DataFrame({'id': [1, 2], 'prediction': [2., np.inf]})
        for ids in ([11], [12], [1, 1], []):
            with self.subTest(ids=ids), self.assertRaises(EvaluationError):
                evaluate_training_mae(truth, pred, split=split(), held_out_ids=ids)
        with self.assertRaises(EvaluationError):
            evaluate_training_mae(truth, pred, split=split(), held_out_ids=[1, 2])

    def test_existing_validation_contract_is_unchanged(self):
        truth = pd.DataFrame({'id': [11], 'loss': [5.]})
        pred = pd.DataFrame({'id': [11], 'prediction': [3.]})
        self.assertEqual(evaluate_mae(truth, pred, split=split())['mae'], 2.)
        with self.assertRaises(EvaluationError):
            evaluate_training_mae(truth, pred, split=split(), held_out_ids=[11])

    def test_partition_reader_skips_poisoned_validation_and_test_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.csv'
            columns = ['id'] + runner.FEATURES + ['loss']
            rows = [[i] + ['A']*116 + [.5]*14 + [float(i)] for i in range(1, 11)]
            rows += [[i] + ['poison']*130 + ['poison'] for i in (11, 12)]
            pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
            frame = runner.read_partition(split(path), split().train_ids)
            self.assertEqual(frame.index.tolist(), list(range(1, 11)))
            self.assertEqual(frame.loss.sum(), 55.)
            with self.assertRaises(EvaluationError):
                runner.read_partition(split(path), [12])

    def test_folds_reject_duplicate_missing_test_and_invalid_labels(self):
        valid = pd.DataFrame({'id': range(1, 11), 'fold': list(range(5))*2})
        self.assertEqual(len(runner.verify_folds(valid, split())), 10)
        for bad in [valid.iloc[:-1], pd.concat([valid, valid.iloc[:1]]),
                    valid.assign(id=[12]+list(range(2, 11))), valid.assign(fold=0),
                    valid.assign(fold=valid.fold.astype(float))]:
            with self.subTest(), self.assertRaises(EvaluationError):
                runner.verify_folds(bad, split())

    def test_selection_applies_one_unit_tie_and_complexity_order(self):
        results = [result('deep', 10., depth=7), result('simple', 10.9, depth=3),
                   result('outside', 11.1, depth=1)]
        self.assertEqual(runner.choose_initial(results), 'simple')
        results = [result('slow', runtime=8), result('fast', runtime=2)]
        self.assertEqual(runner.choose_initial(results), 'fast')

    def test_pending_readiness_blocks_before_source_access_or_output_creation(self):
        with patch.object(runner, 'CONFIG', Path('tests/fixtures/approach2_xgboost_proposed.json')), \
             patch.object(runner, 'real_inputs', side_effect=AssertionError('real source accessed')):
            with self.assertRaisesRegex(EvaluationError, 'training_authorized'):
                runner.main(['check'])

    def test_readiness_requires_all_recorded_decisions_and_hashes(self):
        config = json.loads((runner.ROOT / runner.CONFIG).read_text())
        config['execution']['training_authorized'] = True
        config['policy_review'].update(status='APPROVED', selected_option='amend_to_one_release')
        config['experiment_budget']['resource_deadline'] = '2099-01-01T00:00:00+00:00'
        with tempfile.TemporaryDirectory(dir=runner.ROOT) as directory:
            path = Path(directory)
            evidence = path / 'team-decision.md'
            evidence.write_text('Unit-test fixture only; grants no real approval.\n')
            ref = str(evidence.relative_to(runner.ROOT))
            config['policy_review']['decision_record'] = ref
            decision = {'status': 'APPROVED', 'record': ref, 'sha256': runner.sha256(evidence)}
            rec = {'config_sha256': runner.sha256(runner.ROOT / runner.CONFIG),
                   'release_sequence': 'amend_to_one_release', 'iteration_hypothesis': 'Training CV hypothesis',
                   'minimum_mae_improvement': 1., 'max_runtime_seconds': 100., 'n_jobs': 4,
                   'deadline_utc': config['experiment_budget']['resource_deadline'],
                   'gate1': dict(decision), 'gate2': dict(decision), 'validation_plan': dict(decision)}
            readiness = path / 'readiness.json'
            with patch.object(runner, 'git', return_value=''):
                readiness.write_text(json.dumps(rec))
                self.assertEqual(runner.check_readiness(config, readiness)['n_jobs'], 4)
                rec['gate2']['status'] = 'PENDING'
                readiness.write_text(json.dumps(rec))
                with self.assertRaisesRegex(EvaluationError, 'gate2 readiness'):
                    runner.check_readiness(config, readiness)
                rec['gate2']['status'] = 'APPROVED'
                rec['gate1']['sha256'] = '0'*64
                readiness.write_text(json.dumps(rec))
                with self.assertRaisesRegex(EvaluationError, 'evidence hash'):
                    runner.check_readiness(config, readiness)
                rec['gate1']['sha256'] = runner.sha256(evidence)
                rec['deadline_utc'] = '2000-01-01T00:00:00+00:00'
                readiness.write_text(json.dumps(rec))
                with self.assertRaisesRegex(EvaluationError, 'expired'):
                    runner.check_readiness(config, readiness)

    def test_followup_is_frozen_once_and_changes_one_parameter(self):
        with tempfile.TemporaryDirectory() as directory:
            path, rec = Path(directory), receipt()
            runner.freeze_followup(path, rec, 'max_depth', 4, 'Train OOF suggests underfitting at depth 3')
            plan = json.loads((path / 'followup_plan.json').read_text())
            self.assertEqual(plan['previous_value'], 3)
            self.assertEqual(plan['value'], 4)
            self.assertEqual(rec['stage'], 'FOLLOWUP_FROZEN')
            with self.assertRaises(EvaluationError):
                runner.freeze_followup(path, rec, 'max_depth', 5, 'second try')

    def test_invalid_followup_setting_or_missing_rationale_is_rejected(self):
        for name, value, reason in [('max_depth', 3, 'unchanged'), ('random_state', 7, 'seed'),
                                    ('max_depth', 4, ''), ('max_depth', 4.5, 'fractional depth'),
                                    ('learning_rate', -1, 'negative'), ('learning_rate', np.inf, 'nonfinite')]:
            with self.subTest(name=name, value=value), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(EvaluationError):
                    runner.freeze_followup(Path(directory), receipt(), name, value, reason)

    def test_followup_rejects_changed_plan_and_out_of_sequence_release(self):
        with tempfile.TemporaryDirectory() as directory:
            path, rec = Path(directory), receipt()
            runner.freeze_followup(path, rec, 'max_depth', 4, 'training evidence')
            rec['readiness']['release_sequence'] = 'gate1_two_releases'
            with self.assertRaisesRegex(EvaluationError, 'Release initial'):
                runner.followup(path, rec, {}, None, None, None)
            rec['readiness']['release_sequence'] = 'amend_to_one_release'
            (path / 'followup_plan.json').write_text('{}')
            with self.assertRaisesRegex(EvaluationError, 'plan changed'):
                runner.followup(path, rec, {}, None, None, None)

    def test_failed_fit_consumes_slot_and_is_recorded(self):
        class Prep:
            def fit_transform(self, x): return x
            def transform(self, x): return x
        class BrokenModel:
            def __init__(self, **kwargs): pass
            def fit(self, x, y): raise RuntimeError('deliberate fit failure')
        context, training, folds, _ = runner.synthetic_inputs()
        rec = receipt()
        config = json.loads((runner.ROOT / runner.CONFIG).read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with patch.dict('sys.modules', {'xgboost': types.SimpleNamespace(XGBRegressor=BrokenModel)}), \
                 patch.object(runner, 'load_preprocessor', return_value=Prep()):
                with self.assertRaisesRegex(RuntimeError, 'deliberate'):
                    runner.run_candidate(path, rec, config, config['initial_candidates'][0], context, training, folds)
            self.assertEqual(rec['cv_fits_attempted'], 1)
            self.assertEqual(rec['configurations_attempted'], 1)
            self.assertEqual(rec['results'][-1]['status'], 'FAILED')
            self.assertEqual(json.loads((path / 'run_receipt.json').read_text())['status'], 'FAILED')

    def test_expired_deadline_and_exhausted_runtime_block(self):
        for changes in [{'deadline_utc': '2000-01-01T00:00:00+00:00'}, {'max_runtime_seconds': 0}]:
            rec = receipt()
            rec['readiness'].update(changes)
            with self.assertRaises(EvaluationError):
                runner.resource_check(rec)

    def test_lock_prevents_overlapping_campaign_writers(self):
        with tempfile.TemporaryDirectory() as directory:
            with runner.locked(Path(directory)):
                with self.assertRaises(FileExistsError):
                    with runner.locked(Path(directory)): pass

    def test_intervening_writer_prevents_duplicate_followup_and_validation(self):
        for stage, before, after in [('followup', 'FOLLOWUP_FROZEN', 'FOLLOWUP_COMPLETE'),
                                     ('release', 'FOLLOWUP_COMPLETE', 'COMPLETE')]:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                old = campaign(output, before)
                completed = campaign(output, after)
                runner.write_json(output / 'run_receipt.json', old)
                original_lock = runner.locked

                @contextmanager
                def intervening_writer(path):
                    # A writer finishes before this process can acquire its lock.
                    runner.write_json(path / 'run_receipt.json', completed)
                    with original_lock(path):
                        yield

                def readiness_under_lock(*args):
                    self.assertTrue((output / '.campaign.lock').exists())
                    return old['readiness']

                with patch.object(runner, 'CAMPAIGN', output), \
                     patch.object(runner, 'check_readiness', side_effect=readiness_under_lock), \
                     patch.object(runner, 'locked', intervening_writer), \
                     patch.object(runner, 'real_inputs') as inputs, \
                     patch.object(runner, 'followup') as fit, \
                     patch.object(runner, 'release') as release:
                    with self.assertRaisesRegex(EvaluationError, 'already consumed'):
                        runner.main([stage])
                    inputs.assert_not_called()
                    fit.assert_not_called()
                    release.assert_not_called()
                self.assertEqual(json.loads((output / 'run_receipt.json').read_text()), completed)

    def test_continuation_rechecks_counters_failures_and_input_hashes_under_lock(self):
        for defect in ['counter', 'failure', 'hash', 'readiness']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                rec = campaign(output)
                readiness = deepcopy(rec['readiness'])
                if defect == 'counter': rec['cv_fits_attempted'] = 24
                if defect == 'failure': rec['results'][0]['status'] = 'FAILED'
                if defect == 'hash': rec['frozen_inputs']['source_sha256'] = '0' * 64
                if defect == 'readiness': readiness['minimum_mae_improvement'] = 2.
                runner.write_json(output / 'run_receipt.json', rec)
                with patch.object(runner, 'CAMPAIGN', output), \
                     patch.object(runner, 'check_readiness', return_value=readiness), \
                     patch.object(runner, 'real_inputs') as inputs:
                    with self.assertRaises(EvaluationError):
                        runner.main(['followup'])
                    inputs.assert_not_called()

    def test_initial_environment_mismatch_stops_before_campaign_creation_or_data_access(self):
        for field in ['python', *runner.PACKAGES]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                environment = runner.actual_environment()
                if field == 'python': environment['python'] = '0.0.0'
                else: environment['packages'][field] = '0.0.0'
                output = Path(directory) / 'campaign'
                with patch.object(runner, 'CAMPAIGN', output), \
                     patch.object(runner, 'check_readiness', return_value=receipt()['readiness']), \
                     patch.object(runner, 'actual_environment', return_value=environment), \
                     patch.object(runner, 'real_inputs') as inputs, \
                     patch.object(runner, 'run_candidate') as fit, \
                     patch.object(runner, 'read_partition') as read:
                    with self.assertRaisesRegex(EvaluationError, 'configured interpreter/package'):
                        runner.main(['initial'])
                    self.assertFalse(output.exists())
                    inputs.assert_not_called()
                    fit.assert_not_called()
                    read.assert_not_called()

    def test_continuation_environment_mismatch_stops_under_lock_before_fit_or_validation(self):
        for stage, prior in [('followup', 'FOLLOWUP_FROZEN'), ('release', 'FOLLOWUP_COMPLETE')]:
            for field in ['python', 'implementation', 'executable', *runner.PACKAGES]:
                with self.subTest(stage=stage, field=field), tempfile.TemporaryDirectory() as directory:
                    output = Path(directory)
                    rec = campaign(output, prior)
                    if field in runner.PACKAGES: rec['environment']['packages'][field] = 'OLD'
                    else: rec['environment'][field] = 'OLD'
                    runner.write_json(output / 'run_receipt.json', rec)
                    current = runner.actual_environment()

                    def current_under_lock():
                        self.assertTrue((output / '.campaign.lock').exists())
                        return current

                    with patch.object(runner, 'CAMPAIGN', output), \
                         patch.object(runner, 'check_readiness', return_value=rec['readiness']), \
                         patch.object(runner, 'actual_environment', side_effect=current_under_lock), \
                         patch.object(runner, 'real_inputs') as inputs, \
                         patch.object(runner, 'followup') as fit, \
                         patch.object(runner, 'release') as release, \
                         patch.object(runner, 'read_partition') as read:
                        with self.assertRaisesRegex(EvaluationError, 'Campaign interpreter/package'):
                            runner.main([stage])
                        inputs.assert_not_called()
                        fit.assert_not_called()
                        release.assert_not_called()
                        read.assert_not_called()

    def test_stage_records_actual_environment_and_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            rec = campaign(output, 'INITIAL_COMPLETE')
            runner.write_json(output / 'run_receipt.json', rec)
            argv = ['freeze-followup', '--parameter', 'max_depth', '--value', '4',
                    '--rationale', 'Training-only OOF evidence suggests greater depth']
            with patch.object(runner, 'CAMPAIGN', output), \
                 patch.object(runner, 'check_readiness', return_value=rec['readiness']), \
                 patch.object(runner, 'verify_input_hashes') as hashes, \
                 patch.object(runner, 'real_inputs') as inputs:
                runner.main(argv)
                inputs.assert_not_called()
                hashes.assert_called_once()
            saved = json.loads((output / 'run_receipt.json').read_text())
            event = saved['stage_history'][-1]
            self.assertEqual(event['environment'], runner.actual_environment())
            self.assertEqual(event['command'][4:], argv)
            self.assertEqual(event['status'], 'PASS')
            self.assertEqual(saved['stage'], 'FOLLOWUP_FROZEN')

    def test_source_manifest_and_fold_byte_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate1 = root / 'artifacts/october/gate 1'
            gate1.mkdir(parents=True)
            source, manifest, folds = root / 'generated.csv', gate1 / 'october_partition_manifest.csv', root / 'folds.csv'
            for path in [source, manifest, folds]: path.write_text('synthetic fixture bytes\n')
            (gate1 / 'october_split_metadata.json').write_text(json.dumps({'source': {'path': source.name}}))
            config = {'inputs': {'source_sha256': runner.sha256(source),
                                  'manifest_sha256': runner.sha256(manifest),
                                  'cv_folds_sha256': runner.sha256(folds), 'cv_folds': folds.name}}
            with patch.object(runner, 'ROOT', root):
                runner.verify_input_hashes(config)
                for path in [source, manifest, folds]:
                    path.write_text('changed synthetic bytes\n')
                    with self.subTest(path=path.name), self.assertRaisesRegex(EvaluationError, 'Frozen input file hash changed'):
                        runner.verify_input_hashes(config)
                    path.write_text('synthetic fixture bytes\n')

    def test_synthetic_release_uses_generated_holdout_and_never_fits_it(self):
        context, training, _, validation = runner.synthetic_inputs()
        self.assertEqual(validation.index.tolist(), list(context.validation_ids))
        self.assertTrue(set(context.test_ids).isdisjoint(set(training.index) | set(validation.index)))
        self.assertNotEqual(float(validation.loss.iloc[0]), float(training.loss.iloc[0]))
        config = json.loads((runner.ROOT / runner.CONFIG).read_text())
        calls = {'fit': 0, 'transform': 0, 'predict': 0}
        real_factory = runner.load_preprocessor
        test = self

        class Prep:
            def __init__(self):
                self.inner = real_factory()
                self.named_steps = self.inner.named_steps

            def fit_transform(self, x):
                calls['fit'] += 1
                pd.testing.assert_frame_equal(x, training[runner.FEATURES])
                result = self.inner.fit_transform(x)
                native = self.named_steps['native']
                self.state = deepcopy((native.rare_levels_, native.categories_))
                return result

            def transform(self, x):
                calls['transform'] += 1
                pd.testing.assert_frame_equal(x, validation[runner.FEATURES])
                result = self.inner.transform(x)
                native = self.named_steps['native']
                test.assertEqual((native.rare_levels_, native.categories_), self.state)
                test.assertTrue(pd.isna(result.loc[201, 'cat116']))
                return result

        class Model:
            def __init__(self, **kwargs): pass
            def fit(self, x, y):
                test.assertEqual(x.index.tolist(), list(context.train_ids))
                pd.testing.assert_series_equal(y, training.loss)
            def predict(self, x):
                calls['predict'] += 1
                test.assertEqual(x.index.tolist(), list(context.validation_ids))
                return np.ones(len(x))
            def save_model(self, path): Path(path).write_text('{}')
            def load_model(self, path): pass

        original_score = runner.evaluate_mae
        def score(truth, predictions, **kwargs):
            pd.testing.assert_frame_equal(truth, validation[['loss']].rename_axis('id').reset_index())
            return original_score(truth, predictions, **kwargs)

        rec = receipt()
        rec.update(stage='FOLLOWUP_COMPLETE', synthetic=True, final_candidate='A2-C01')
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runner, 'load_preprocessor', side_effect=Prep), \
                 patch.dict('sys.modules', {'xgboost': types.SimpleNamespace(XGBRegressor=Model)}), \
                 patch.object(runner, 'read_partition', side_effect=AssertionError('source accessed')), \
                 patch.object(runner, 'evaluate_mae', side_effect=score):
                runner.release(Path(directory), rec, config, context, training, synthetic_validation=validation)
        self.assertEqual(calls, {'fit': 1, 'transform': 2, 'predict': 2})

    def test_synthetic_release_rejects_missing_or_test_fixture_before_fit(self):
        context, training, _, validation = runner.synthetic_inputs()
        poisoned = validation.copy()
        poisoned.index = list(context.test_ids)
        poisoned.loc[:, 'loss'] = np.nan
        for invalid in [None, poisoned, training.iloc[:1]]:
            with self.subTest(), tempfile.TemporaryDirectory() as directory:
                rec = receipt()
                rec.update(stage='FOLLOWUP_COMPLETE', synthetic=True, final_candidate='A2-C01')
                with patch.dict('sys.modules', {'xgboost': types.SimpleNamespace(XGBRegressor=object)}), \
                     patch.object(runner, 'load_preprocessor') as prep, \
                     patch.object(runner, 'read_partition') as read:
                    with self.assertRaises(EvaluationError):
                        runner.release(Path(directory), rec, {}, context, training, synthetic_validation=invalid)
                    prep.assert_not_called()
                    read.assert_not_called()
                    self.assertEqual(rec['releases'], {})

    def test_config_budget_cannot_be_expanded_silently(self):
        config = json.loads((runner.ROOT / runner.CONFIG).read_text())
        runner.validate_config(config)
        config['experiment_budget']['maximum_cv_fits'] = 35
        with self.assertRaises(EvaluationError):
            runner.validate_config(config)


if __name__ == '__main__':
    unittest.main()
