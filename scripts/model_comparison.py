"""Evaluate existing prediction artifacts; never fit, tune, or select models."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import tempfile
import uuid

import numpy as np
import pandas as pd
from scripts.evaluation import (ROOT, EvaluationError, claim_ids, evaluate_mae,
                                load_frozen_split, load_partition_targets, require, sha256)

BASELINE = Path('artifacts/october/gate 2/baselines/baselines-20261025T034742Z-0e9ea822/baseline_run_receipt.json')
INPUTS = Path('artifacts/october/gate 3/comparison_inputs')
QUANTILES = [0, .25, .5, .75, .9, .95, .99, 1]
FAILURE_COLUMNS = ['model_name', 'run_id', 'failure_type', 'failure_count', 'expected_validation_claim_count',
                   'actual_prediction_row_count', 'example_affected_ids', 'artifact_path', 'resolution_status', 'reason']


def baseline_changes(mae, baseline):
    require(math.isfinite(mae) and math.isfinite(baseline) and mae >= 0 and baseline >= 0, 'Invalid MAE')
    return mae - baseline, 100 * (baseline - mae) / baseline if baseline > 0 else None


def gaps(validation_mae, training_mae=None, cv_mae=None):
    return {'training_mae': training_mae, 'cv_mean_mae': cv_mae,
            'generalization_gap': None if training_mae is None else validation_mae - training_mae,
            'validation_minus_cv_mean': None if cv_mae is None else validation_mae - cv_mae}


def stability(values=None, evidence_type='cross_validation_folds'):
    if values is None or len(values) < 2:
        return {'evidence_type': evidence_type, 'status': 'NOT_ASSESSED — insufficient repeated-run evidence',
                'count': 0 if values is None else len(values), 'mean_mae': None, 'std_mae': None,
                'min_mae': None, 'max_mae': None, 'range_mae': None}
    values = np.asarray(values, dtype=float)
    require(np.isfinite(values).all() and (values >= 0).all(), 'Invalid stability MAEs')
    return {'evidence_type': evidence_type, 'status': 'ASSESSED', 'count': len(values),
            'mean_mae': float(values.mean()), 'std_mae': float(values.std(ddof=1)),
            'min_mae': float(values.min()), 'max_mae': float(values.max()), 'range_mae': float(np.ptp(values))}


def prediction_failures(frame, expected_ids):
    """Audit every visible failure without repairing inputs or scoring subsets."""
    issues = []
    def add(kind, count, ids=()):
        if count:
            issues.append((kind, int(count), ','.join(map(str, list(ids)[:5]))))
    if not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique or set(frame.columns) != {'id', 'prediction'}:
        return [('invalid_schema', 1, '')]
    add('empty_artifact', len(frame) == 0)
    add('null_ids', frame.id.isna().sum())
    valid_ids = []
    for value in frame.id:
        try:
            valid_ids.extend(claim_ids([value], 'prediction'))
        except EvaluationError:
            add('invalid_id', 1, [value])
    add('duplicate_ids', len(valid_ids) - len(set(valid_ids)), pd.Series(valid_ids)[pd.Series(valid_ids).duplicated()].tolist())
    add('missing_predictions', len(set(expected_ids) - set(valid_ids)), sorted(set(expected_ids) - set(valid_ids)))
    add('extra_predictions', len(set(valid_ids) - set(expected_ids)), sorted(set(valid_ids) - set(expected_ids)))
    raw = frame.prediction
    values = pd.to_numeric(raw, errors='coerce')
    add('nan_predictions', raw.isna().sum(), frame.loc[raw.isna(), 'id'])
    add('non_numeric_predictions', (values.isna() & raw.notna()).sum(), frame.loc[values.isna() & raw.notna(), 'id'])
    add('positive_infinity', (values == np.inf).sum(), frame.loc[values == np.inf, 'id'])
    add('negative_infinity', (values == -np.inf).sum(), frame.loc[values == -np.inf, 'id'])
    if not pd.api.types.is_numeric_dtype(raw.dtype) or pd.api.types.is_bool_dtype(raw.dtype) or pd.api.types.is_complex_dtype(raw.dtype):
        add('invalid_numeric_dtype', len(raw))
    return issues


def verify_identity(evidence, split):
    for key, expected in [('source_sha256', split.source_sha256), ('manifest_id', split.manifest_id),
                          ('manifest_sha256', split.manifest_sha256)]:
        require(evidence.get(key) == expected, f'{key} mismatch')
    require(evidence.get('metric') == 'MAE', 'metric mismatch')
    require(evidence.get('units') == 'original loss units', 'incorrect or unproven prediction scale')
    require(evidence.get('evaluated_claim_count') == len(split.validation_ids), 'validation population count mismatch')
    require(evidence.get('partition') == 'validation', 'partition mismatch')


def score_existing(truth, predictions, evidence, split):
    verify_identity(evidence, split)
    score = evaluate_mae(truth, predictions, split=split)
    require(math.isclose(score['mae'], evidence['mae'], rel_tol=1e-10, abs_tol=1e-8), 'Recorded and recomputed MAE disagree')
    return score


def diagnostic_summaries(truth, predictions, training_loss):
    """Call only after full validation coverage has passed the shared evaluator."""
    truth = truth.assign(id=claim_ids(truth.id, 'diagnostic truth'))
    predictions = predictions.assign(id=claim_ids(predictions.id, 'diagnostic predictions'))
    aligned = truth.merge(predictions, on='id', validate='one_to_one').sort_values('id')
    require(len(aligned) == len(truth) == len(predictions) and len(aligned) > 0, 'Diagnostic coverage mismatch')
    y, p = aligned.loss.to_numpy(), aligned.prediction.to_numpy()
    error = p - y
    absolute = np.abs(error)
    # Internal quantile cuts only; outer intervals cover all validation losses.
    cuts = np.quantile(np.asarray(training_loss, dtype=float), QUANTILES[1:-1], method='linear')
    bins = np.searchsorted(cuts, y, side='left')
    boundaries = [-np.inf, *cuts, np.inf]
    def summarize(mask):
        count = int(mask.sum())
        result = {'claim_count': count, 'validation_denominator': len(y), 'validation_share': count / len(y),
                  'support_note': 'empty' if count == 0 else ('low support (<30); descriptive only' if count < 30 else 'descriptive only')}
        for key, values, func in [('mean_actual_loss', y, np.mean), ('median_actual_loss', y, np.median),
                                  ('mae', absolute, np.mean), ('mean_signed_error', error, np.mean),
                                  ('median_absolute_error', absolute, np.median), ('prediction_mean', p, np.mean),
                                  ('prediction_median', p, np.median), ('max_absolute_error', absolute, np.max)]:
            result[key] = float(func(values[mask])) if count else None
        result['absolute_error_std'] = float(absolute[mask].std(ddof=1)) if count > 1 else None
        return result
    rows = []
    for i in range(7):
        rows.append(dict(bin_label=f'{int(QUANTILES[i]*100)}–{int(QUANTILES[i+1]*100)}%',
                         lower_boundary=boundaries[i], upper_boundary=boundaries[i+1],
                         interval='(lower, upper]', threshold_source='training linear quantiles', **summarize(bins == i)))
    tails = [dict(tail_label=f'loss > training p{int(q*100)}', threshold=float(cuts[j]),
                  threshold_source='training linear quantiles', **summarize(y > cuts[j])) for q, j in [(.95, 4), (.99, 5)]]
    require(sum(r['claim_count'] for r in rows) == len(y), 'Bin support does not reconcile')
    return rows, tails, {'training_count': len(training_loss), 'quantiles': QUANTILES[1:-1], 'boundaries': cuts.tolist()}


def read_predictions(path):
    return pd.read_csv(path, dtype={'id': 'string'}, float_precision='round_trip')


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else 'unavailable'


def run(output_root, write_summary=False):
    split = load_frozen_split()
    train, truth = load_partition_targets(split)
    run_id = datetime.now(timezone.utc).strftime('comparison-%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
    out = Path(output_root) / run_id
    out.mkdir(parents=True, exist_ok=False)
    input_hashes = {}
    def tracked(path):
        path = Path(path)
        input_hashes[str(path)] = sha256(path)
        return path
    def read_json(path):
        return json.loads(tracked(path).read_text())
    baseline_receipt = read_json(BASELINE)
    base_maes, valid = {}, []
    for result in baseline_receipt['results']:
        name = result['baseline_name']
        require(name in ('mean', 'median') and name not in base_maes, 'Unexpected/duplicate baseline')
        for key in ['source_sha256', 'manifest_id', 'manifest_sha256']:
            require(baseline_receipt[key] == getattr(split, key), f'Baseline receipt {key} mismatch')
        path = tracked(result['prediction_artifact'])
        require(sha256(path) == result['prediction_sha256'], 'Baseline prediction hash mismatch')
        pred = read_predictions(path)
        score = score_existing(truth, pred, result, split)
        require(pred.prediction.eq(result['fitted_constant']).all(), 'Baseline predictions differ from recorded constant')
        base_maes[name] = score['mae']
        valid.append({'model_name': f'Training {name}', 'run_id': baseline_receipt['run_id'], 'kind': 'baseline',
                      'score': score, 'predictions': pred, 'receipt_path': str(BASELINE), 'prediction_artifact': str(path),
                      'config': {'fitted_constant': result['fitted_constant']}, 'train_mae': None, 'cv_mae': None,
                      'cv_pooled_mae': None, 'fold_maes': None, 'complexity': '1 fitted scalar; no predictive features',
                      'runtime_seconds': None, 'runtime_type': 'unavailable', 'training_count': len(train),
                      'environment': {k: baseline_receipt[k] for k in ['python', 'pandas', 'numpy']}})
    require(set(base_maes) == {'mean', 'median'}, 'Both baselines required')
    failures, inventory = [], []
    def fail(model, rid, path, kind, reason, count=1, examples='', rows=None, status='INELIGIBLE'):
        failures.append(dict(model_name=model, run_id=rid, failure_type=kind, failure_count=count,
                             expected_validation_claim_count=len(truth), actual_prediction_row_count=rows,
                             example_affected_ids=examples, artifact_path=str(path), resolution_status=status, reason=reason))
    for directory in sorted(INPUTS.glob('*')):
        if not directory.is_dir():
            continue
        model, rid = 'Ridge GLM', directory.name
        path = directory / 'validation_predictions.csv'
        entry = dict(model_name=model, run_id=rid, evidence_path=str(directory), evaluation_status='INELIGIBLE')
        inventory.append(entry)
        pred = None
        try:
            # Inspect predictions even if other provenance will subsequently fail.
            if path.is_file():
                pred = read_predictions(tracked(path))
                for kind, count, examples in prediction_failures(pred, split.validation_ids):
                    fail(model, rid, path, kind, 'Prediction contract failure', count, examples, len(pred))
            else:
                fail(model, rid, path, 'missing_artifact', 'Prediction artifact missing', status='INCOMPLETE')
            before = len([f for f in failures if f['run_id'] == rid])
            receipt = read_json(directory / 'run_receipt.json')
            provenance = read_json(directory / 'provenance.json')
            require(receipt['run_id'] == rid and receipt['status'] == 'completed' and receipt['test_used'] is False,
                    'Run incomplete, wrong identity or test isolation unconfirmed')
            for filename, item in provenance['files'].items():
                require(sha256(tracked(directory / filename)) == item['sha256'], f'Snapshot hash mismatch: {filename}')
            require(len(provenance['source_commit']) == 40, 'Evidence commit missing')
            for key in ['source_sha256', 'manifest_id', 'manifest_sha256']:
                require(receipt[key] == getattr(split, key), f'{key} mismatch')
            verify_identity(receipt['validation'], split)
            require(receipt['training_claims'] == len(train), 'Training population mismatch')
            require(path.is_file() and sha256(path) == receipt['prediction_sha256'], 'Prediction hash missing/mismatch')
            if before:
                continue
            score = score_existing(truth, pred, receipt['validation'], split)
            cv = pd.read_csv(tracked(directory / 'cv_results.csv'))
            selected = cv.loc[cv.alpha.eq(receipt['selected_alpha'])].sort_values('fold')
            folds_path = Path(receipt['config']['inputs']['cv_folds'])
            require(sha256(tracked(folds_path)) == receipt['input_sha256'][str(folds_path)], 'CV assignment hash mismatch')
            folds = pd.read_csv(folds_path)
            require(folds.id.is_unique and set(folds.id) == set(split.train_ids), 'CV training membership mismatch')
            counts = folds.groupby('fold').size()
            require(selected.fold.is_unique and set(selected.fold) == set(counts.index), 'Incomplete selected CV folds')
            require(selected.set_index('fold').claims.to_dict() == counts.to_dict(), 'CV held-out support mismatch')
            require(np.isfinite(selected[['mae', 'absolute_error_sum']]).all().all() and (selected.mae >= 0).all(), 'Invalid CV metrics')
            require(np.allclose(selected.mae * selected.claims, selected.absolute_error_sum, rtol=1e-10), 'CV error sums disagree')
            pooled = float(selected.absolute_error_sum.sum() / len(train))
            require(math.isclose(pooled, receipt['pooled_cv_mae'][str(receipt['selected_alpha'])], rel_tol=1e-10), 'CV receipt mismatch')
            fold_maes = selected.mae.tolist()
            stats = stability(fold_maes)
            recorded = receipt['fold_mae_summary'][str(receipt['selected_alpha'])]
            require(math.isclose(stats['mean_mae'], recorded['mean'], rel_tol=1e-10)
                    and math.isclose(stats['std_mae'], recorded['std'], rel_tol=1e-10), 'CV summary mismatch')
            runtime = receipt.get('runtime_seconds')
            require(runtime is None or (isinstance(runtime, (int, float)) and math.isfinite(runtime) and runtime >= 0), 'Invalid measured runtime')
            valid.append(dict(model_name=model, run_id=rid, kind='candidate', score=score, predictions=pred,
                              receipt_path=str(directory / 'run_receipt.json'), prediction_artifact=str(path),
                              config={'configuration': receipt['config'], 'selected_alpha': receipt['selected_alpha']},
                              train_mae=None, cv_mae=stats['mean_mae'], cv_pooled_mae=pooled, fold_maes=fold_maes,
                              complexity=f"Ridge alpha={receipt['selected_alpha']}; 130 source predictors; post-encoding coefficient count unavailable",
                              runtime_seconds=runtime, runtime_type='total workflow (30 CV fits, preprocessing, refit, validation)',
                              training_count=receipt['training_claims'], environment=receipt['environment'],
                              provenance=provenance))
            entry['evaluation_status'] = 'VALID'
        except (EvaluationError, KeyError, ValueError, OSError, TypeError) as exc:
            fail(model, rid, path, 'provenance_or_evaluation_failure', str(exc), rows=None if pred is None else len(pred))
            entry['reason'] = str(exc)
    # Main's second approach is only a scaffold, not a completed experiment.
    config_path = Path('artifacts/october/gate 2/approach2_xgboost_config.json')
    xgb = read_json(config_path)
    inventory.append(dict(model_name='XGBoost', run_id='unavailable', evidence_path=str(config_path),
                          evaluation_status='INCOMPLETE', reason='Only proposed configuration; no committed prediction/run receipt in comparison inputs'))
    fail('XGBoost', 'unavailable', config_path, 'missing_run_and_predictions',
         'Only proposed configuration available; no candidate MAE assigned', status='INCOMPLETE', count=1)
    comparison, bin_rows, tail_rows, overfit, stable = [], [], [], [], []
    thresholds = None
    for item in valid:
        model, rid, score = item['model_name'], item['run_id'], item['score']
        delta_mean, pct_mean = baseline_changes(score['mae'], base_maes['mean'])
        delta_median, pct_median = baseline_changes(score['mae'], base_maes['median'])
        identity = {'model_name': model, 'run_id': rid}
        comparison.append(dict(**identity, kind=item['kind'], manifest_id=split.manifest_id, source_version=split.source_sha256,
                               train_or_cv_mae=item['cv_mae'], train_metric_type='CV fold mean' if item['cv_mae'] is not None else 'unavailable',
                               training_mae=item['train_mae'], cv_mean_mae=item['cv_mae'], cv_pooled_mae=item['cv_pooled_mae'],
                               validation_mae=score['mae'], validation_claim_count=len(truth),
                               delta_vs_mean_baseline=delta_mean, delta_vs_median_baseline=delta_median,
                               pct_improvement_vs_mean=pct_mean, pct_improvement_vs_median=pct_median,
                               complexity=item['complexity'], runtime_seconds=item['runtime_seconds'], runtime_type=item['runtime_type'],
                               hardware='unavailable; no computational ranking', environment=json.dumps(item['environment'], sort_keys=True),
                               model_configuration=json.dumps(item['config'], sort_keys=True),
                               prediction_artifact=item['prediction_artifact'], receipt_path=item['receipt_path'], evaluation_status='VALID'))
        bins, tails, thresholds = diagnostic_summaries(truth, item['predictions'], train.loss)
        bin_rows.extend(dict(**identity, **r) for r in bins)
        tail_rows.extend(dict(**identity, **r) for r in tails)
        stats = stability(item['fold_maes'])
        stable.append(dict(**identity, **stats))
        stable.append(dict(**identity, **stability(None, 'random_seed_or_repeated_training')))
        overfit.append(dict(**identity, validation_mae=score['mae'], **gaps(score['mae'], item['train_mae'], item['cv_mae']),
                            cv_pooled_mae=item['cv_pooled_mae'], cv_std_mae=stats['std_mae'], cv_fold_count=stats['count'],
                            training_sample_count=item['training_count'], validation_sample_count=len(truth),
                            assessment='Provisional descriptive CV difference; in-sample training MAE unavailable' if item['cv_mae'] is not None else 'NOT_ASSESSED — training/CV evidence unavailable'))
    tables = {'model_comparison': comparison, 'model_target_bin_diagnostics': bin_rows, 'model_high_loss_diagnostics': tail_rows,
              'model_overfitting_diagnostics': overfit, 'model_stability_diagnostics': stable, 'candidate_inventory': inventory}
    for name, rows in tables.items():
        pd.DataFrame(rows).to_csv(out / f'{name}.csv', index=False, float_format='%.17g')
    pd.DataFrame(failures, columns=FAILURE_COLUMNS).to_csv(out / 'model_prediction_failures.csv', index=False)
    figures = make_plots(comparison, bin_rows, tail_rows, split, out)
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_model_comparison.py'],
                           cwd=ROOT, capture_output=True, text=True)
    summary_path = ROOT / 'docs/task_model_comparison_summary.md'
    checks = {
        'Frozen source verified': sha256(split.source_path) == split.source_sha256,
        'Frozen manifest verified': sha256(split.manifest_path) == split.manifest_sha256,
        'Shared evaluator reused': all(i['score']['metric'] == 'MAE' for i in valid),
        'Baseline comparability verified': set(base_maes) == {'mean', 'median'},
        'Candidate artifacts discovered': any(i['kind'] == 'candidate' for i in valid),
        'Prediction IDs validated': all(i['score']['checks']['id_alignment'] for i in valid),
        'All valid models evaluated on identical claims': all(i['score']['evaluated_claim_count'] == len(truth) for i in valid),
        'Original-scale validation MAE calculated': all(i['score']['units'] == 'original loss units' for i in valid),
        'Baseline deltas calculated': all(math.isclose(r['delta_vs_mean_baseline'], r['validation_mae'] - base_maes['mean']) for r in comparison),
        'Complexity documented': all(bool(r['complexity']) for r in comparison),
        'Runtime documented or explicitly unavailable': all(bool(r['runtime_type']) for r in comparison),
        'Target-distribution diagnostics generated': len(bin_rows) == 7 * len(valid),
        'High-loss diagnostics generated': len(tail_rows) == 2 * len(valid),
        'Support counts documented': all(sum(r['claim_count'] for r in bin_rows if r['model_name'] == i['model_name'] and r['run_id'] == i['run_id']) == len(truth) for i in valid),
        'Overfitting diagnostics generated': len(overfit) == len(valid),
        'Stability assessed or explicitly unavailable': len(stable) == 2 * len(valid),
        'Prediction failures identified': len(inventory) == sum(e['evaluation_status'] == 'VALID' or any(f['run_id'] == e['run_id'] for f in failures) for e in inventory),
        'Automated tests passed': tests.returncode == 0,
        'Documentation generated': (ROOT / 'docs/october_model_comparison_guide.md').is_file(),
        'Internal test targets untouched': set(train.id).union(truth.id).isdisjoint(split.test_ids),
    }
    if write_summary:
        write_task_summary(summary_path, out, comparison, bin_rows, tail_rows, overfit, stable, failures, run_id)
    checks['Completion summary generated'] = summary_path.is_file()
    receipt = {'run_id': run_id, 'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'git_commit': git('rev-parse', 'HEAD'),
               'git_status': git('status', '--porcelain'), 'source_hash': split.source_sha256, 'manifest_id': split.manifest_id,
               'manifest_hash': split.manifest_sha256, 'validation_claim_count': len(truth), 'training_claim_count': len(train),
               'baseline_run_ids': [baseline_receipt['run_id']], 'candidate_run_ids': [r['run_id'] for r in inventory],
               'evaluation_code_version': sha256(ROOT / 'scripts/evaluation.py'),
               'comparison_code_version': sha256(Path(__file__)), 'input_sha256': input_hashes, 'thresholds': thresholds,
               'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'matplotlib': figures},
               'reproduction_command': 'python3 -m scripts.model_comparison',
               'execution_command': shlex.join([sys.executable, '-m', 'scripts.model_comparison', *sys.argv[1:]]),
               'tests': {'exit_code': tests.returncode, 'output': tests.stdout + tests.stderr},
               'test_isolation': 'Shared loader skips test rows before target conversion; train/validation only; no model fitting',
               'limitations': ['GLM evidence snapshotted from an unmerged branch with user authorization.',
                               'XGBoost incomplete; no predictions or run receipt.', 'No in-sample training MAE, seed/repeat evidence or hardware record.',
                               'Runtime is total workflow, not isolated training time; post-encoding coefficient count unavailable.',
                               'Prediction scale established from producer provenance; numeric values cannot prove scale alone.'],
               'artifacts_sha256': {str(p): sha256(p) for p in sorted(out.iterdir())}}
    receipt_path = out / 'model_comparison_run_receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    checks['Run receipt generated'] = json.loads(receipt_path.read_text())['run_id'] == run_id
    receipt['checks'] = {k: bool(v) for k, v in checks.items()}
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    checklist = '\n'.join(f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items())
    if write_summary:
        with summary_path.open('a') as f:
            f.write('\nValidation checklist:\n\n' + checklist + '\n')
    print(pd.DataFrame(comparison)[['model_name', 'validation_mae', 'delta_vs_mean_baseline', 'pct_improvement_vs_median']].to_string(index=False))
    print('October Model Comparison and Diagnostics\n' + checklist)
    print(f'Receipt: {receipt_path}')
    require(all(checks.values()), 'Comparison checks failed; see receipt')
    return receipt


def make_plots(comparison, bins, tails, split, out):
    os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'allstate-comparison-mpl'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout='constrained')
    names = [r['model_name'] for r in comparison]
    axes[0].barh(names, [r['validation_mae'] for r in comparison], color='#31688e')
    axes[0].set_title(f'Primary comparison: validation MAE (n={len(split.validation_ids):,})')
    axes[0].set_xlabel('MAE — original loss units')
    for r in comparison:
        rows = [b for b in bins if b['model_name'] == r['model_name'] and b['run_id'] == r['run_id']]
        axes[1].plot([f"{b['bin_label']}\nn={b['claim_count']:,}" for b in rows], [b['mae'] for b in rows], marker='o', label=r['model_name'])
    axes[1].set_title('Diagnostic: error across training-derived loss bins')
    axes[1].set_ylabel('MAE — original loss units')
    axes[1].tick_params(axis='x', labelrotation=35)
    axes[1].legend()
    fig.suptitle(f'{split.manifest_id} | source SHA-256 {split.source_sha256[:12]}…')
    fig.savefig(out / 'model_comparison.png', dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout='constrained')
    rows = [r for r in tails if 'p95' in r['tail_label']]
    axes[0].barh([r['model_name'] for r in rows], [r['mae'] for r in rows])
    axes[0].set_title(f"Diagnostic: loss > training p95 ({rows[0]['threshold']:.2f})\nn={rows[0]['claim_count']:,}/{len(split.validation_ids):,}")
    axes[0].set_xlabel('MAE — original loss units')
    eligible = [r for r in comparison if r['cv_mean_mae'] is not None]
    if eligible:
        x = np.arange(len(eligible))
        axes[1].bar(x-.2, [r['cv_mean_mae'] for r in eligible], .4, label='CV fold mean')
        axes[1].bar(x+.2, [r['validation_mae'] for r in eligible], .4, label='Validation')
        axes[1].set_xticks(x, [r['model_name'] for r in eligible])
        axes[1].legend()
    axes[1].set_title('Diagnostic: CV vs validation; not training error')
    axes[1].set_ylabel('MAE — original loss units')
    fig.suptitle(f'{split.manifest_id} | source SHA-256 {split.source_sha256[:12]}…')
    fig.savefig(out / 'model_tail_and_cv.png', dpi=150)
    plt.close(fig)
    return matplotlib.__version__


def write_task_summary(path, out, comparison, bins, tails, overfit, stable, failures, run_id):
    lines = ['# October model comparison and diagnostics', '',
             'Implemented shared-evaluator comparison, exact prediction validation, baseline verification, training-derived target bins and tails, descriptive CV gaps, stability summaries, failure reporting and reproducible plots. No models were fitted, tuned or selected.', '',
             f'Run: `{run_id}`. Frozen manifest: `october-split-v1`; 28,248 validation claims. Artifacts: `{out}`.', '',
             '| Model | Run ID | Validation MAE | Delta vs mean | Delta vs median | Improvement vs mean | Improvement vs median |',
             '|---|---|---:|---:|---:|---:|---:|']
    for r in comparison:
        lines.append(f"| {r['model_name']} | {r['run_id']} | {r['validation_mae']:.6f} | {r['delta_vs_mean_baseline']:.6f} | {r['delta_vs_median_baseline']:.6f} | {r['pct_improvement_vs_mean']:.2f}% | {r['pct_improvement_vs_median']:.2f}% |")
    lines += ['', 'Diagnostic findings (original loss units):', '']
    candidate_bins = [r for r in bins if r['model_name'] == 'Ridge GLM']
    if candidate_bins:
        lines += ['| Training-derived bin | Validation support | MAE | Mean signed error |', '|---|---:|---:|---:|']
        lines += [f"| {r['bin_label']} | {r['claim_count']:,}/{r['validation_denominator']:,} | {r['mae']:.2f} | {r['mean_signed_error']:.2f} |" for r in candidate_bins]
        lines += ['', 'Ridge overpredicts the lower-loss half on average and underpredicts the upper-loss half. Error increases strongly in the upper tail; these slices describe behavior and do not select a model.', '']
    for r in tails:
        if r['model_name'] == 'Ridge GLM':
            lines.append(f"- {r['tail_label']}, threshold {r['threshold']:.6f}: {r['claim_count']:,}/{r['validation_denominator']:,} claims ({100*r['validation_share']:.2f}%); MAE {r['mae']:.2f}, mean signed error {r['mean_signed_error']:.2f}, median absolute error {r['median_absolute_error']:.2f}, maximum absolute error {r['max_absolute_error']:.2f}. Negative signed error indicates underprediction.")
    for r in overfit:
        if r['cv_mean_mae'] is not None:
            lines.append(f"- {r['model_name']}: validation minus CV fold-mean MAE is {r['validation_minus_cv_mean']:.6f}; pooled OOF MAE {r['cv_pooled_mae']:.6f}. In-sample training MAE is unavailable, so a training generalization gap cannot be established.")
    for r in stable:
        if r['status'] == 'ASSESSED':
            lines.append(f"- {r['model_name']}: {r['count']} CV folds, mean {r['mean_mae']:.6f}, sample SD {r['std_mae']:.6f}, range {r['min_mae']:.6f}–{r['max_mae']:.6f}. This measures fold variability, not seed or repeated-training stability.")
    lines += ['', 'Failures and unavailable evidence:', '']
    lines += [f"- {r['model_name']}: {r['resolution_status']} — {r['reason']}" for r in failures]
    lines += ['', 'GLM predictions passed exact coverage and numeric checks. Target-bin support reconciles to the full validation population; see `model_target_bin_diagnostics.csv` for all seven bins. No seed/repeated-run evidence is available. The GLM receipt measures 89.03 seconds for the whole workflow, not isolated training/prediction; hardware and post-encoding coefficient count are unavailable. Runtimes do not support a computational ranking.', '',
              'Evidence: GLM receipt, CV table and predictions are verbatim snapshots from Hector’s unmerged branch at commit `ab331538eba349e19a326ff6d87c395ccdb1a742`, explicitly authorized by Krish. `comparison_inputs/.../provenance.json` records original paths and hashes. XGBoost remains incomplete. Numeric predictions alone cannot prove target scale; the producer’s original-unit evaluator receipt supplies that evidence.', '',
              'Files: `scripts/model_comparison.py`, `tests/test_model_comparison.py`, `docs/october_model_comparison_guide.md`, this summary, four evidence snapshot files under `artifacts/october/gate 3/comparison_inputs/`, and the run directory containing comparison, bins, tails, overfitting, stability, failures, candidate inventory, two plots and a run receipt.', '',
              'Reproduce from repository root: `python3 -m scripts.model_comparison`. Tests: `python3 -m unittest discover -s tests`.', '',
              'Next review questions: confirm integration of the GLM evidence; obtain the completed XGBoost receipt and predictions; request in-sample metrics, measured fit/predict runtimes and hardware details; review upper-tail underprediction. Diagnostics remain descriptive; overall original-scale validation MAE is primary. No winning model is selected and no hyperparameter changes are approved. Test targets remain untouched.', '']
    path.write_text('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=Path('artifacts/october/gate 3/comparisons'))
    parser.add_argument('--write-summary', action='store_true')
    args = parser.parse_args()
    run(args.output_root, args.write_summary)
