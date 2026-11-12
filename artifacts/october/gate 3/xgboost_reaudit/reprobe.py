"""Repeat the original three audit scenarios against the fixed runner.

Run from any folder with --output NEW_JSON_PATH. Fixtures and CLI readiness
mocks are confined to temporary directories; no real source is opened/fitted.
The original audit/reproducer is deliberately preserved separately.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts import run_xgboost as r


def ledger(output, stage):
    config = json.loads((ROOT / r.CONFIG).read_text())
    ready = {'release_sequence': 'amend_to_one_release', 'minimum_mae_improvement': 1.,
             'deadline_utc': '2099-01-01T00:00:00+00:00', 'max_runtime_seconds': 120}
    rec = r.new_receipt(config, ready, synthetic=False)
    rec.update(stage=stage, initial_winner='A2-C01', final_candidate='A2-C01',
               configurations_attempted=5, cv_fits_attempted=25,
               frozen_inputs={'source_sha256': config['inputs']['source_sha256'],
                              'manifest_sha256': config['inputs']['manifest_sha256'],
                              'cv_folds_sha256': config['inputs']['cv_folds_sha256'],
                              'training_claims': config['evaluation']['training_claims']})
    rec['results'] = [{'id': c['id'], 'status': 'PASS', 'parameters': r.model_params(config, c),
                       'fold_results': [{'fold': f, 'claims': 1, 'mae': 1.} for f in range(5)]}
                      for c in config['initial_candidates']]
    if stage in {'FOLLOWUP_COMPLETE', 'COMPLETE'}:
        rec['results'].append(dict(deepcopy(rec['results'][0]), id='A2-C06'))
        rec.update(configurations_attempted=6, cv_fits_attempted=30)
    if stage == 'COMPLETE':
        rec['releases']['final'] = {'status': 'PASS'}
    plan = output / 'followup_plan.json'
    if not plan.exists():
        r.write_json(plan, {'note': 'temporary ledger-only probe fixture'}, new=True)
    rec['followup_plan_sha256'] = r.sha256(plan)
    return rec


def expect_blocked(stage, output, rec, *, lock=None):
    patches = {'CAMPAIGN': output, 'check_readiness': lambda *_: rec['readiness']}
    if lock is not None:
        patches['locked'] = lock
    with patch.multiple(r, **patches), patch.object(r, 'real_inputs') as inputs, \
         patch.object(r, 'followup') as fit, patch.object(r, 'release') as score:
        try:
            r.main([stage])
        except r.EvaluationError as exc:
            error = str(exc)
        else:
            raise AssertionError('Continuation was accepted')
        r.require(not inputs.called and not fit.called and not score.called,
                  'Rejected continuation accessed data, fitting or validation dispatch')
    return error


def probe_lock():
    results = []
    for stage, before, after in [('followup', 'FOLLOWUP_FROZEN', 'FOLLOWUP_COMPLETE'),
                                 ('release', 'FOLLOWUP_COMPLETE', 'COMPLETE')]:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            rec, completed = ledger(output, before), ledger(output, after)
            r.write_json(output / 'run_receipt.json', rec)
            original_lock = r.locked

            @contextmanager
            def other_writer_finishes(path):
                r.write_json(path / 'run_receipt.json', completed)
                with original_lock(path):
                    yield

            error = expect_blocked(stage, output, rec, lock=other_writer_finishes)
            r.require('already consumed' in error, error)
            r.require(json.loads((output / 'run_receipt.json').read_text()) == completed,
                      'Current ledger was overwritten')
            results.append({'command': stage, 'status': 'BLOCKED', 'reason': error,
                            'data_fit_validation_dispatches': 0, 'current_ledger_preserved': True})
    return results


def probe_environment():
    results = []
    for stage, state in [('followup', 'FOLLOWUP_FROZEN'), ('release', 'FOLLOWUP_COMPLETE')]:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            rec = ledger(output, state)
            rec['environment']['packages']['xgboost'] = 'DIFFERENT_FROM_CURRENT_ENVIRONMENT'
            r.write_json(output / 'run_receipt.json', rec)
            error = expect_blocked(stage, output, rec)
            r.require('Campaign interpreter/package environment changed' in error, error)
            results.append({'command': stage, 'status': 'BLOCKED', 'reason': error,
                            'data_fit_validation_dispatches': 0})
    return results


def probe_validation():
    split, training, _, validation = r.synthetic_inputs()
    observed = {'preprocessor_fit_ids': [], 'transform_ids': [], 'model_fit_ids': [], 'truth_matches_holdout': False}

    class Prep:
        named_steps = {'native': types.SimpleNamespace(rare_levels_={}, categories_={})}
        def fit_transform(self, x):
            observed['preprocessor_fit_ids'] = x.index.tolist()
            return x
        def transform(self, x):
            r.pd.testing.assert_frame_equal(x, validation[r.FEATURES])
            observed['transform_ids'].append(x.index.tolist())
            return x

    class Model:
        def __init__(self, **kwargs): pass
        def fit(self, x, y):
            observed['model_fit_ids'] = x.index.tolist()
            r.pd.testing.assert_series_equal(y, training.loss)
        def predict(self, x): return r.np.ones(len(x))
        def save_model(self, path): Path(path).write_text('{}')
        def load_model(self, path): pass

    evaluator = r.evaluate_mae
    def score(truth, predictions, **kwargs):
        r.pd.testing.assert_frame_equal(truth, validation[['loss']].rename_axis('id').reset_index())
        observed['truth_matches_holdout'] = True
        return evaluator(truth, predictions, **kwargs)

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        rec = ledger(output, 'FOLLOWUP_COMPLETE')
        rec['synthetic'] = True
        with patch.dict('sys.modules', {'xgboost': types.SimpleNamespace(XGBRegressor=Model)}), \
             patch.object(r, 'load_preprocessor', return_value=Prep()), \
             patch.object(r, 'read_partition', side_effect=AssertionError('source accessed')), \
             patch.object(r, 'evaluate_mae', side_effect=score):
            r.release(output, rec, {}, split, training, synthetic_validation=validation)
    r.require(observed['preprocessor_fit_ids'] == observed['model_fit_ids'] == list(split.train_ids),
              'Fit population differs from training fixture')
    r.require(observed['transform_ids'] == [list(split.validation_ids)] * 2
              and observed['truth_matches_holdout'], 'Holdout fixture not used transform-only')
    r.require(float(validation.loss.iloc[0]) != float(training.loss.iloc[0]), 'Holdout target was relabeled')
    r.require(set(split.test_ids).isdisjoint(set(training.index) | set(validation.index)), 'Test fixture exposed')
    return {'status': 'PASS', 'fit_claims': len(training), 'validation_ids': list(validation.index),
            'features_and_target_match_separate_fixture': True, 'validation_transform_only': True,
            'test_features_and_target_not_generated': True, 'real_source_accesses': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'scope': 'Synthetic temporary fixtures only', 'code_sha256': r.code_hashes(),
              'lock': probe_lock(), 'environment': probe_environment(), 'validation': probe_validation()}
    r.write_json(args.output, report, new=True)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
