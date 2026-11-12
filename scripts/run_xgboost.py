"""October Approach 2: bounded, staged XGBoost experiment; synthetic by default.

Real training requires both the team's updated config and a recorded readiness
file. See docs/october_xgboost_guide.md. Importing this module loads no ML library.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import types

import numpy as np
import pandas as pd

from scripts.evaluation import (ROOT, FrozenSplit, EvaluationError, checked_frame, claim_ids,
                                evaluate_mae, evaluate_training_mae,
                                load_frozen_split, require, sha256)

CONFIG = Path('artifacts/october/gate 2/approach2_xgboost_config.json')
CAMPAIGN = Path('artifacts/october/gate 3/runs/xgboost-task4')
NOTEBOOK = Path('notebooks/gate2_preprocessing.ipynb')
CATS = [f'cat{i}' for i in range(1, 117)]
CONTS = [f'cont{i}' for i in range(1, 15)]
FEATURES = CATS + CONTS
CHANGEABLE = {'max_depth', 'learning_rate', 'n_estimators', 'min_child_weight',
              'subsample', 'colsample_bytree', 'reg_lambda', 'max_cat_threshold'}
PACKAGES = ('numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost')


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value, *, new=False):
    text = json.dumps(value, indent=2, allow_nan=False) + '\n'
    if new:
        with Path(path).open('x') as handle:
            handle.write(text)
    else:
        temporary = Path(path).with_suffix('.tmp')
        temporary.write_text(text)
        temporary.replace(path)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def code_hashes():
    return {p: sha256(ROOT / p) for p in
            ['scripts/run_xgboost.py', 'scripts/evaluation.py', str(NOTEBOOK)]}


def actual_environment():
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'executable': str(Path(sys.executable).resolve()),
            'packages': {name: version(name) for name in PACKAGES}}


def check_environment(config, environment):
    """The adopted config pins the interpreter version and fitting libraries."""
    expected = config['environment']
    require(environment['python'] == expected['python']
            and environment['packages'] == {name: expected[name] for name in PACKAGES},
            'Environment differs from configured interpreter/package versions; no fit or validation access authorized')


def validate_config(config):
    b = config['experiment_budget']
    require((b['initial_configurations'], b['reserved_iteration_configurations'],
             b['max_configurations'], b['cv_folds_per_configuration'], b['maximum_cv_fits'])
            == (5, 1, 6, 5, 30), 'Only the checked-in 5+1 / 30-fit budget is supported')
    require(b['early_stopping'] is False and b['maximum_final_refits'] == 2,
            'Early stopping/refit budget differs')
    candidates = config['initial_candidates']
    require(len(candidates) == 5 and len({c['id'] for c in candidates}) == 5,
            'Require five distinct initial candidate IDs')
    require(all(set(c) == {'id', 'max_depth', 'learning_rate'} for c in candidates),
            'Initial candidates may vary only depth and learning rate')
    require(config['target']['transform'] == 'identity'
            and config['model']['objective'] == 'reg:absoluteerror'
            and config['model']['eval_metric'] == 'mae'
            and config['model']['tree_method'] == 'hist'
            and config['model']['enable_categorical'] is True,
            'Require native categorical original-unit absolute-error XGBoost')
    require(config['model']['random_state'] == 42
            and config['preprocessing']['rare_min_count'] == 30,
            'Frozen seed/rare rule differs')


def check_readiness(config, path):
    """Fail closed before loading any real rows or creating a campaign."""
    require(config['execution']['training_authorized'] is True,
            'BLOCKED: config execution.training_authorized is false; team readiness is pending')
    policy = config['policy_review']
    require(policy['status'] == 'APPROVED'
            and policy['selected_option'] in {'gate1_two_releases', 'amend_to_one_release'}
            and bool(policy['decision_record']), 'BLOCKED: release sequence not approved/recorded')
    require(path is not None, 'BLOCKED: --readiness must name the recorded team decision')
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'Readiness must be recorded inside this worktree')
    git('ls-files', '--error-unmatch', str(path.relative_to(ROOT)))
    record = json.loads(path.read_text())
    require(record['config_sha256'] == sha256(ROOT / CONFIG), 'Readiness config hash differs')
    require(record['release_sequence'] == policy['selected_option'], 'Readiness release sequence differs')
    require(record['iteration_hypothesis'].strip(), 'Record a training-only iteration hypothesis')
    require(np.isfinite(record['minimum_mae_improvement']) and record['minimum_mae_improvement'] > 0,
            'Record a finite positive keep threshold in loss units')
    require(np.isfinite(record['max_runtime_seconds']) and record['max_runtime_seconds'] > 0,
            'Record the finite positive resource/runtime limit')
    for name in ['gate1', 'gate2', 'validation_plan']:
        decision = record[name]
        require(decision['status'] == 'APPROVED', f'BLOCKED: {name} readiness is pending')
        evidence = (ROOT / decision['record']).resolve()
        require(evidence.is_relative_to(ROOT), 'Decision evidence must be repository-local')
        git('ls-files', '--error-unmatch', str(evidence.relative_to(ROOT)))
        require(sha256(evidence) == decision['sha256'], f'{name} evidence hash differs')
    require(policy['decision_record'] == record['validation_plan']['record'],
            'Config and readiness must identify the same validation decision')
    deadline = datetime.fromisoformat(record['deadline_utc'])
    require(deadline.tzinfo is not None and deadline > datetime.now(timezone.utc),
            'BLOCKED: resource deadline is missing, naive or expired')
    require(config['experiment_budget']['resource_deadline'] == record['deadline_utc'],
            'Config and readiness deadlines differ')
    require(record['n_jobs'] == config['model']['n_jobs'], 'Resource thread count differs')
    return {**record, 'readiness_sha256': sha256(path)}


def load_preprocessor():
    """Load Hector's actual definitions, without notebook data loads or writes."""
    from sklearn.pipeline import Pipeline
    notebook = json.loads((ROOT / NOTEBOOK).read_text())
    source = '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code')
    names = {'validate_feature_schema', 'FeatureSchemaValidator', 'NativeCategoricalPreprocessor'}
    body = [n for n in ast.parse(source).body if isinstance(n, (ast.Import, ast.ImportFrom))
            or isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
    require({n.name for n in body if isinstance(n, (ast.ClassDef, ast.FunctionDef))} == names,
            'Notebook preprocessing definitions missing')
    module = types.ModuleType('october_xgboost_preprocessing')
    sys.modules[module.__name__] = module
    exec(compile(ast.Module(body=body, type_ignores=[]), str(NOTEBOOK), 'exec'), module.__dict__)
    return Pipeline([('schema', module.FeatureSchemaValidator(FEATURES, CONTS)),
                     ('native', module.NativeCategoricalPreprocessor(CATS, 30))])


def read_partition(split, ids):
    """Skip all other rows before converting predictors or loss, including test."""
    import csv
    ids = claim_ids(ids, 'requested partition')
    require(set(ids) in (set(split.train_ids), set(split.validation_ids)), 'Unsupported partition')
    wanted, records = set(ids), []
    with split.source_path.open(newline='') as handle:
        for row in csv.DictReader(handle):
            i = int(row['id'])
            if i not in wanted:
                continue
            records.append([i] + [row[c] for c in CATS]
                           + [float(row[c]) for c in CONTS] + [float(row['loss'])])
    frame = pd.DataFrame(records, columns=['id'] + FEATURES + ['loss']).set_index('id')
    require(frame.index.is_unique and set(frame.index) == wanted, 'Partition ID coverage differs')
    checked_frame(frame.reset_index()[['id', 'loss']], 'loss', ids, 'partition targets')
    frame[CATS] = frame[CATS].astype('string')
    return frame.sort_index()


def verify_folds(folds, split):
    require(list(folds.columns) == ['id', 'fold'], 'Unexpected saved fold schema')
    ids = claim_ids(folds.id, 'CV folds')
    require(set(ids) == set(split.train_ids), 'Saved folds must cover only training IDs exactly once')
    require(pd.api.types.is_integer_dtype(folds.fold.dtype)
            and set(folds.fold) == set(range(5)), 'Require saved integer folds 0 through 4')
    counts = folds.fold.value_counts()
    require(counts.max() - counts.min() <= 1, 'Saved folds are not balanced')
    return folds.set_index('id').sort_index()


def real_inputs(config):
    split = load_frozen_split()
    inputs = config['inputs']
    require((split.source_sha256, split.manifest_sha256, split.manifest_id) ==
            (inputs['source_sha256'], inputs['manifest_sha256'], inputs['split_manifest']),
            'Config and frozen split identities differ')
    path = ROOT / inputs['cv_folds']
    require(sha256(path) == inputs['cv_folds_sha256'], 'Saved CV hash mismatch')
    folds = verify_folds(pd.read_csv(path), split)
    return split, read_partition(split, split.train_ids), folds


def verify_input_hashes(config):
    """Recheck frozen bytes under the campaign lock without parsing targets."""
    gate1 = ROOT / 'artifacts/october/gate 1'
    metadata = json.loads((gate1 / 'october_split_metadata.json').read_text())
    paths = [(ROOT / metadata['source']['path'], config['inputs']['source_sha256']),
             (gate1 / 'october_partition_manifest.csv', config['inputs']['manifest_sha256']),
             (ROOT / config['inputs']['cv_folds'], config['inputs']['cv_folds_sha256'])]
    for path, expected in paths:
        require(sha256(path) == expected, 'Frozen input file hash changed; no fit or validation access authorized')


def synthetic_inputs():
    """Return training and a distinct validation fixture; no test row is generated."""
    rng = np.random.default_rng(42)
    ids = np.arange(1, 202)
    frame = pd.DataFrame({c: rng.choice(['A', 'B', 'C', 'RARE'], len(ids), p=[.45,.3,.23,.02])
                          for c in CATS}, index=ids)
    for c in CONTS:
        frame[c] = rng.random(len(ids))
    frame['loss'] = 100 + 500 * frame.cont1 + 80 * (frame.cat1 == 'B') + rng.normal(0, 5, len(ids))
    frame[CATS] = frame[CATS].astype('string')
    split = FrozenSplit(Path('synthetic-only.csv'), '0'*64, Path('synthetic-manifest.csv'),
                        '1'*64, 'synthetic-only', tuple(range(1, 201)), (201,), (202,), '2'*64, '3'*64)
    # A category present only in held-out fold 0 tests the learned missing branch.
    frame.loc[1, 'cat1'] = 'FOLD0_ONLY'
    frame.loc[201, 'cat116'] = 'VALIDATION_ONLY'
    folds = verify_folds(pd.DataFrame({'id': ids[:200], 'fold': np.arange(200) % 5}), split)
    return (split, frame.loc[list(split.train_ids)].copy(), folds,
            frame.loc[list(split.validation_ids)].copy())


def model_params(config, candidate):
    return {k: v for k, v in {**config['model'], **candidate}.items() if k not in {'id', 'estimator'}}


def choose_initial(results):
    best = min(r['pooled_oof_mae'] for r in results)
    eligible = [r for r in results if r['pooled_oof_mae'] <= best + 1]
    return min(eligible, key=lambda r: (r['parameters']['max_depth'], r['parameters']['n_estimators'],
                                      r['parameters']['learning_rate'], r['runtime_seconds']))['id']


def save_receipt(output, receipt):
    failed = any(r['status'] == 'FAILED' for r in receipt['results'] + list(receipt['releases'].values()))
    failed = failed or any(e['status'] == 'FAILED' for e in receipt.get('stage_history', []))
    receipt['status'] = 'FAILED' if failed else ('COMPLETE' if receipt['stage'] == 'COMPLETE' else receipt['stage'])
    receipt['updated_utc'] = now()
    write_json(output / 'run_receipt.json', receipt)


def resource_check(receipt):
    limits = receipt['readiness']
    require(datetime.now(timezone.utc) < datetime.fromisoformat(limits['deadline_utc']),
            'Resource deadline reached; no more fits authorized')
    require(receipt['fit_runtime_seconds'] < limits['max_runtime_seconds'], 'Runtime budget exhausted')


def run_candidate(output, receipt, config, candidate, split, training, folds):
    from xgboost import XGBRegressor
    require(receipt['configurations_attempted'] < 6, 'Configuration budget exhausted')
    receipt['configurations_attempted'] += 1
    result = {'id': candidate['id'], 'parameters': model_params(config, candidate),
              'status': 'RUNNING', 'started_utc': now(), 'fold_results': []}
    receipt['results'].append(result)
    save_receipt(output, receipt)
    start = time.monotonic()
    try:
        predictions = []
        for fold in range(5):
            resource_check(receipt)
            require(receipt['cv_fits_attempted'] < 30, 'CV fit budget exhausted')
            held = folds.index[folds.fold.eq(fold)].tolist()
            fit = folds.index[~folds.fold.eq(fold)].tolist()
            prep = load_preprocessor()
            x_fit = prep.fit_transform(training.loc[fit, FEATURES])
            x_held = prep.transform(training.loc[held, FEATURES])
            model = XGBRegressor(**result['parameters'])
            resource_check(receipt)
            receipt['cv_fits_attempted'] += 1
            save_receipt(output, receipt)  # Failed fits and interrupted attempts consume slots.
            tick = time.monotonic()
            try:
                model.fit(x_fit, training.loc[fit, 'loss'])
                pred = pd.DataFrame({'id': held, 'prediction': model.predict(x_held)})
            finally:
                receipt['fit_runtime_seconds'] += time.monotonic() - tick
                save_receipt(output, receipt)
            truth = training.loc[held, ['loss']].rename_axis('id').reset_index()
            score = evaluate_training_mae(truth, pred, split=split, held_out_ids=held)
            result['fold_results'].append({'fold': fold, 'claims': len(held), 'mae': score['mae'],
                                           'fit_predict_seconds': time.monotonic() - tick})
            predictions.append(pred.assign(fold=fold))
            save_receipt(output, receipt)
        oof = pd.concat(predictions).sort_values('id')
        truth = training[['loss']].rename_axis('id').reset_index()
        score = evaluate_training_mae(truth, oof[['id', 'prediction']], split=split,
                                      held_out_ids=split.train_ids)
        path = output / f"{candidate['id']}_oof.csv"
        oof.to_csv(path, index=False, float_format='%.17g')
        values = [r['mae'] for r in result['fold_results']]
        result.update(status='PASS', pooled_oof_mae=score['mae'], checks=score['checks'],
                      fold_mean_mae=float(np.mean(values)), fold_sample_sd=float(np.std(values, ddof=1)),
                      prediction_sha256=sha256(path), prediction_count=len(oof),
                      negative_prediction_count=int((oof.prediction < 0).sum()))
    except BaseException as exc:
        result.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        result['runtime_seconds'] = time.monotonic() - start
        save_receipt(output, receipt)
    return result


def freeze_followup(output, receipt, parameter, value, rationale):
    require(receipt['stage'] == 'INITIAL_COMPLETE', 'Initial CV must finish before freezing follow-up')
    if receipt['readiness']['release_sequence'] == 'gate1_two_releases':
        require(receipt['releases'].get('initial', {}).get('status') == 'PASS',
                'Release the initial comparison before freezing the follow-up')
    require(parameter in CHANGEABLE and rationale and rationale.strip(), 'Supply one allowed setting and a reason')
    selected = next(r for r in receipt['results'] if r['id'] == receipt['initial_winner'])
    require(value != selected['parameters'][parameter], 'Follow-up must change exactly one setting')
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and np.isfinite(value) and value > 0, 'Follow-up setting must be a finite positive number')
    if parameter in {'max_depth', 'n_estimators', 'max_cat_threshold'}:
        require(isinstance(value, int), 'Tree counts/depth/category thresholds must be integers')
    if parameter in {'subsample', 'colsample_bytree', 'learning_rate'}:
        require(value <= 1, 'Rate/fraction must not exceed 1')
    plan = {'id': 'A2-C06', 'parent': selected['id'], 'parameter': parameter, 'value': value,
            'previous_value': selected['parameters'][parameter], 'rationale': rationale,
            'evidence': 'Initial training-only pooled OOF and per-fold results in run_receipt.json',
            'before_pooled_oof_mae': selected['pooled_oof_mae'], 'frozen_utc': now(),
            'minimum_mae_improvement': receipt['readiness']['minimum_mae_improvement']}
    write_json(output / 'followup_plan.json', plan, new=True)
    receipt.update(stage='FOLLOWUP_FROZEN', followup_plan_sha256=sha256(output / 'followup_plan.json'))
    save_receipt(output, receipt)


def followup(output, receipt, config, split, training, folds):
    require(receipt['stage'] == 'FOLLOWUP_FROZEN', 'Freeze the one-setting rationale first')
    if receipt['readiness']['release_sequence'] == 'gate1_two_releases':
        require('initial' in receipt['releases'], 'Release initial comparison before the follow-up fit')
    plan_path = output / 'followup_plan.json'
    require(sha256(plan_path) == receipt['followup_plan_sha256'], 'Frozen follow-up plan changed')
    plan = json.loads(plan_path.read_text())
    parent = next(r for r in receipt['results'] if r['id'] == plan['parent'])
    candidate = {**parent['parameters'], 'id': 'A2-C06', plan['parameter']: plan['value']}
    result = run_candidate(output, receipt, config, candidate, split, training, folds)
    improvement = parent['pooled_oof_mae'] - result['pooled_oof_mae']
    keep = improvement >= plan['minimum_mae_improvement']
    receipt.update(stage='FOLLOWUP_COMPLETE', comparison={
        'before_id': parent['id'], 'after_id': result['id'], 'before_pooled_oof_mae': parent['pooled_oof_mae'],
        'after_pooled_oof_mae': result['pooled_oof_mae'], 'improvement': improvement,
        'keep_followup': keep, 'reason': 'Training-only improvement compared with the recorded keep threshold'},
        final_candidate=result['id'] if keep else parent['id'])
    save_receipt(output, receipt)


def release(output, receipt, config, split, training, *, synthetic_validation=None):
    from xgboost import XGBRegressor
    sequence = receipt['readiness']['release_sequence']
    initial = sequence == 'gate1_two_releases' and not receipt['releases']
    require(receipt['stage'] in ({'INITIAL_COMPLETE', 'FOLLOWUP_FROZEN'} if initial else {'FOLLOWUP_COMPLETE'}),
            'Release is out of sequence')
    label = 'initial' if initial else 'final'
    require(label not in receipt['releases'], 'This validation release was already attempted')
    candidate_id = receipt['initial_winner'] if initial else (
        'A2-C06' if sequence == 'gate1_two_releases' else receipt['final_candidate'])
    candidate = next(r for r in receipt['results'] if r['id'] == candidate_id)
    if receipt['synthetic']:
        require(isinstance(synthetic_validation, pd.DataFrame), 'Supply the separate synthetic validation fixture')
        valid = synthetic_validation.copy()
        require(list(valid.columns) == FEATURES + ['loss']
                and training.index.is_unique and set(training.index) == set(split.train_ids)
                and set(valid.index).isdisjoint(training.index), 'Synthetic holdout/train schema or membership differs')
        checked_frame(valid[['loss']].rename_axis('id').reset_index(), 'loss',
                      split.validation_ids, 'synthetic validation fixture')
    else:
        require(synthetic_validation is None, 'Real release cannot accept a synthetic validation fixture')
    resource_check(receipt)
    require(len(receipt['releases']) < (2 if sequence == 'gate1_two_releases' else 1), 'Refit/release budget exhausted')
    item = {'candidate_id': candidate_id, 'status': 'RUNNING', 'started_utc': now()}
    receipt['releases'][label] = item
    save_receipt(output, receipt)
    tick = time.monotonic()
    try:
        prep = load_preprocessor()
        x_fit = prep.fit_transform(training[FEATURES])
        model = XGBRegressor(**candidate['parameters'])
        resource_check(receipt)
        model.fit(x_fit, training.loss)
        if not receipt['synthetic']:
            valid = read_partition(split, split.validation_ids)
        pred = pd.DataFrame({'id': valid.index, 'prediction': model.predict(prep.transform(valid[FEATURES]))})
        truth = valid[['loss']].rename_axis('id').reset_index()
        score = evaluate_mae(truth, pred, split=split)
        pred.to_csv(output / f'{label}_validation_predictions.csv', index=False, float_format='%.17g')
        model.save_model(output / f'{label}_model.json')
        restored = XGBRegressor()
        restored.load_model(output / f'{label}_model.json')
        require(np.array_equal(restored.predict(prep.transform(valid[FEATURES])), pred.prediction.to_numpy()),
                'Serialized model prediction round trip differs')
        native = prep.named_steps['native']
        write_json(output / f'{label}_preprocessing.json', {
            'schema': FEATURES, 'continuous': CONTS, 'rare_min_count': 30,
            'rare_levels': native.rare_levels_, 'categories': native.categories_,
            'notebook_sha256': sha256(ROOT / NOTEBOOK)}, new=True)
        item.update(status='PASS', validation_mae=score['mae'], claims=len(valid), model_round_trip=True)
        item['artifact_sha256'] = {p.name: sha256(p) for p in output.glob(f'{label}_*') if p.is_file()}
        if label == 'final':
            receipt['stage'] = 'COMPLETE'
            if 'initial' in receipt['releases']:
                receipt['comparison']['before_validation_mae'] = receipt['releases']['initial']['validation_mae']
                receipt['comparison']['after_validation_mae'] = score['mae']
    except BaseException as exc:
        item.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        item['runtime_seconds'] = time.monotonic() - tick
        receipt['fit_runtime_seconds'] += item['runtime_seconds']
        save_receipt(output, receipt)


@contextmanager
def locked(output):
    path = output / '.campaign.lock'
    with path.open('x') as handle:
        handle.write(f'{now()}\n')
    try:
        yield
    finally:
        path.unlink()


@contextmanager
def record_stage(output, receipt, stage, environment, command):
    event = {'stage': stage, 'started_utc': now(), 'environment': environment,
             'command': command, 'status': 'RUNNING'}
    receipt.setdefault('stage_history', []).append(event)
    save_receipt(output, receipt)
    tick = time.monotonic()
    try:
        yield
    except BaseException as exc:
        event.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
        raise
    else:
        event['status'] = 'PASS'
    finally:
        event.update(ended_utc=now(), runtime_seconds=time.monotonic() - tick)
        save_receipt(output, receipt)


def new_receipt(config, readiness, *, synthetic, environment=None):
    environment = actual_environment() if environment is None else environment
    return {'run_id': 'xgboost-task4-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'),
            'started_utc': now(), 'synthetic': synthetic, 'status': 'RUNNING', 'stage': 'INITIAL_RUNNING',
            'branch': git('branch', '--show-current'),
            'git_commit': git('rev-parse', 'HEAD'), 'git_status': git('status', '--porcelain', '--untracked-files=all'),
            'command': sys.argv, 'code_sha256': code_hashes(), 'config_sha256': sha256(ROOT / CONFIG),
            'config': config, 'effective_config_sha256': hashlib.sha256(
                json.dumps(config, sort_keys=True).encode()).hexdigest(),
            'readiness': readiness, 'python': environment['python'], 'versions': environment['packages'],
            'environment': environment, 'stage_history': [],
            'configurations_attempted': 0, 'cv_fits_attempted': 0, 'fit_runtime_seconds': 0,
            'results': [], 'releases': {}, 'test_partition': 'Never loaded, fitted, tuned, or evaluated'}


def initial(output, receipt, config, split, training, folds):
    for candidate in config['initial_candidates']:
        run_candidate(output, receipt, config, candidate, split, training, folds)
    receipt.update(stage='INITIAL_COMPLETE', initial_winner=choose_initial(receipt['results']))
    save_receipt(output, receipt)


def validate_campaign(output, receipt, config, readiness, stage, environment):
    """Validate the current ledger while its lock is held, before loading data."""
    require(receipt['config_sha256'] == sha256(ROOT / CONFIG)
            and receipt['code_sha256'] == code_hashes()
            and receipt['readiness'] == readiness and receipt['synthetic'] is False,
            'Campaign inputs/code/readiness changed; obtain a written amendment before continuing')
    require(receipt.get('environment') == environment
            and receipt['python'] == environment['python'] and receipt['versions'] == environment['packages'],
            'Campaign interpreter/package environment changed; no fit or validation access authorized')
    require(all(r['status'] == 'PASS' for r in receipt['results'])
            and all(r['status'] == 'PASS' for r in receipt['releases'].values())
            and all(e['status'] == 'PASS' for e in receipt.get('stage_history', [])),
            'Failed/interrupted attempts consume budget; automatic retries are disabled')
    configurations, fits = receipt['configurations_attempted'], receipt['cv_fits_attempted']
    require(type(configurations) is int and type(fits) is int
            and 0 <= configurations <= 6 and 0 <= fits <= 30,
            'Invalid or exhausted campaign counters')
    require(configurations == len(receipt['results']) and fits == 5 * configurations
            and all(len(r['fold_results']) == 5
                    and {f['fold'] for f in r['fold_results']} == set(range(5))
                    for r in receipt['results']), 'Campaign counters disagree with completed folds')
    expected_ids = [c['id'] for c in config['initial_candidates']]
    if configurations == 6:
        expected_ids.append('A2-C06')
    require([r['id'] for r in receipt['results']] == expected_ids,
            'Campaign candidate history differs from the frozen search')
    expected_inputs = {'source_sha256': config['inputs']['source_sha256'],
                       'manifest_sha256': config['inputs']['manifest_sha256'],
                       'cv_folds_sha256': config['inputs']['cv_folds_sha256'],
                       'training_claims': config['evaluation']['training_claims']}
    require(receipt['frozen_inputs'] == expected_inputs, 'Campaign frozen input identities changed')
    sequence = readiness['release_sequence']
    if stage == 'freeze-followup':
        allowed, expected_count = {'INITIAL_COMPLETE'}, 5
        releases = {'initial'} if sequence == 'gate1_two_releases' else set()
    elif stage == 'followup':
        allowed, expected_count = {'FOLLOWUP_FROZEN'}, 5
        releases = {'initial'} if sequence == 'gate1_two_releases' else set()
    else:
        require(stage == 'release', 'Unknown continuation stage')
        is_initial = sequence == 'gate1_two_releases' and not receipt['releases']
        allowed, expected_count = ({'INITIAL_COMPLETE'}, 5) if is_initial else ({'FOLLOWUP_COMPLETE'}, 6)
        releases = set() if is_initial or sequence == 'amend_to_one_release' else {'initial'}
    require(receipt['stage'] in allowed and configurations == expected_count
            and set(receipt['releases']) == releases,
            'Stage already consumed or out of sequence; no additional fit or validation release authorized')
    if receipt['stage'] in {'FOLLOWUP_FROZEN', 'FOLLOWUP_COMPLETE'}:
        require(sha256(output / 'followup_plan.json') == receipt['followup_plan_sha256'],
                'Frozen follow-up plan changed')
    resource_check(receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['check', 'smoke', 'initial', 'freeze-followup', 'followup', 'release'])
    parser.add_argument('--readiness', type=Path)
    parser.add_argument('--output', type=Path, help='Synthetic smoke output only; must not already exist')
    parser.add_argument('--smoke-sequence', choices=['amend_to_one_release', 'gate1_two_releases'],
                        default='amend_to_one_release')
    parser.add_argument('--parameter', choices=sorted(CHANGEABLE))
    parser.add_argument('--value', type=json.loads)
    parser.add_argument('--rationale')
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(argv)
    command = [sys.executable, '-B', '-m', 'scripts.run_xgboost', *argv]
    config = json.loads((ROOT / CONFIG).read_text())
    validate_config(config)
    if args.stage == 'smoke':
        require(args.output is not None, 'Supply a fresh --output directory for synthetic evidence')
        environment = actual_environment()
        check_environment(config, environment)
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
        config = json.loads(json.dumps(config))
        config['model'].update(n_estimators=4, n_jobs=1)
        readiness = {'release_sequence': args.smoke_sequence, 'minimum_mae_improvement': .01,
                     'deadline_utc': '2099-01-01T00:00:00+00:00', 'max_runtime_seconds': 120}
        receipt = new_receipt(config, readiness, synthetic=True, environment=environment)
        split, training, folds, validation = synthetic_inputs()
        validation_path = output / 'synthetic_validation_fixture.csv'
        validation.rename_axis('id').reset_index().to_csv(validation_path, index=False, float_format='%.17g')
        receipt['synthetic_fixture'] = {'training_claims': len(training), 'validation_claims': len(validation),
                                        'validation_sha256': sha256(validation_path),
                                        'test': 'ID reserved; test features and target never generated or returned'}
        with locked(output):
            with record_stage(output, receipt, 'initial', environment, command):
                initial(output, receipt, config, split, training, folds)
            if args.smoke_sequence == 'gate1_two_releases':
                with record_stage(output, receipt, 'release-initial', environment, command):
                    release(output, receipt, config, split, training, synthetic_validation=validation)
            with record_stage(output, receipt, 'freeze-followup', environment, command):
                freeze_followup(output, receipt, 'n_estimators', 6,
                                'Synthetic workflow probe: test two extra boosting rounds after initial OOF comparison.')
            with record_stage(output, receipt, 'followup', environment, command):
                followup(output, receipt, config, split, training, folds)
            with record_stage(output, receipt, 'release-final', environment, command):
                release(output, receipt, config, split, training, synthetic_validation=validation)
        print(f'SYNTHETIC PASS: 6 configurations, 30 CV fits, {len(receipt["releases"])} artificial validation release(s); {output}')
        return
    if args.stage == 'check':
        check_readiness(config, args.readiness)
        check_environment(config, actual_environment())
        print('Recorded readiness/config checks passed; no source rows loaded or models fitted')
        return
    require(args.output is None, 'Real experiments use one fixed campaign directory to preserve the budget ledger')
    output = ROOT / CAMPAIGN
    if args.stage == 'initial':
        # Reject pending decisions without creating a real campaign directory.
        # All decisions/configuration are reloaded under the lock before use.
        check_readiness(config, args.readiness)
        check_environment(config, actual_environment())
        output.mkdir(parents=True, exist_ok=False)
    with locked(output):
        config = json.loads((ROOT / CONFIG).read_text())
        validate_config(config)
        readiness = check_readiness(config, args.readiness)
        environment = actual_environment()
        check_environment(config, environment)
        if args.stage == 'initial':
            receipt = new_receipt(config, readiness, synthetic=False, environment=environment)
            save_receipt(output, receipt)
        else:
            receipt = json.loads((output / 'run_receipt.json').read_text())
            validate_campaign(output, receipt, config, readiness, args.stage, environment)
        with record_stage(output, receipt, args.stage, environment, command):
            verify_input_hashes(config)
            if args.stage == 'freeze-followup':
                freeze_followup(output, receipt, args.parameter, args.value, args.rationale)
            else:
                split, training, folds = real_inputs(config)
                receipt['frozen_inputs'] = {'source_sha256': split.source_sha256,
                                            'manifest_sha256': split.manifest_sha256,
                                            'cv_folds_sha256': config['inputs']['cv_folds_sha256'],
                                            'training_claims': len(training)}
                if args.stage == 'initial':
                    initial(output, receipt, config, split, training, folds)
                elif args.stage == 'followup':
                    followup(output, receipt, config, split, training, folds)
                else:
                    release(output, receipt, config, split, training)
    print(f"{receipt['stage']}: {output}")


if __name__ == '__main__':
    try:
        main()
    except EvaluationError as exc:
        sys.exit(str(exc))
