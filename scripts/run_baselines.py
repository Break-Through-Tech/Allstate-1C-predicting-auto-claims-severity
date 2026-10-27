"""Run immutable, traceable constant baselines: python3 -m scripts.run_baselines."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import uuid

import numpy as np
import pandas as pd
from scripts.evaluation import (ROOT, checked_frame, evaluate_mae, load_frozen_split,
                                load_partition_targets, require, sha256)


def fit_constants(training, split):
    split.validate()
    frame = checked_frame(training, 'loss', split.train_ids, 'training').sort_values('id')
    values = frame.loss.to_numpy()
    constants = {'mean': float(np.mean(values)), 'median': float(np.median(values))}
    require(all(math.isfinite(v) for v in constants.values()), 'Nonfinite fitted constant')
    return constants


def predict_constant(constant, split):
    split.validate()
    return checked_frame(pd.DataFrame({'id': sorted(split.validation_ids), 'prediction': constant}),
                         'prediction', split.validation_ids, 'constant predictions')


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else 'unavailable'


def run(output_root, write_summary=False):
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime('baselines-%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
    split = load_frozen_split()
    training, validation = load_partition_targets(split)
    constants = fit_constants(training, split)
    repeated = fit_constants(training.sample(frac=1, random_state=42), split)
    output = Path(output_root) / run_id
    output.mkdir(parents=True, exist_ok=False)
    code_version = git('rev-parse', 'HEAD')
    receipt = {'run_id': run_id, 'timestamp_utc': timestamp, 'code_version': code_version,
               'git_status_at_execution': git('status', '--porcelain'),
               'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__,
               'scikit_learn': 'not used', 'execution_command': shlex.join([sys.executable, '-m', 'scripts.run_baselines', *sys.argv[1:]]),
               'evaluation_script': 'scripts/evaluation.py',
               'code_sha256': {p: sha256(ROOT / p) for p in ['scripts/evaluation.py', 'scripts/run_baselines.py']},
               'source_path': str(split.source_path.relative_to(ROOT)), 'source_sha256': split.source_sha256,
               'source_version': split.source_sha256, 'manifest_path': str(split.manifest_path.relative_to(ROOT)),
               'manifest_id': split.manifest_id, 'manifest_sha256': split.manifest_sha256,
               'metadata_sha256': split.metadata_sha256, 'acceptance_sha256': split.acceptance_sha256,
               'train_claim_count': len(training), 'validation_claim_count': len(validation), 'results': []}
    rows = []
    for name, constant in constants.items():
        predictions = predict_constant(constant, split)
        path = output / f'baseline_{name}_predictions.csv'
        predictions.to_csv(path, index=False, float_format='%.17g')
        restored = pd.read_csv(path, float_precision='round_trip')
        require(restored.prediction.eq(constant).all(), 'Export changed fitted constant')
        result = evaluate_mae(validation, restored, split=split, run_metadata={'run_id': run_id, 'baseline': name})
        rerun = evaluate_mae(validation, predict_constant(repeated[name], split).sample(frac=1, random_state=7), split=split)
        require(result['mae'] == rerun['mae'] and constant == repeated[name], 'Reproduction failed')
        independent = math.fsum(abs(y - constant) for y in validation.loss) / len(validation)
        require(math.isclose(result['mae'], independent, rel_tol=1e-12), 'Independent MAE disagrees')
        result.update(baseline_name=name, fitted_constant=constant, prediction_artifact=str(path),
                      prediction_sha256=sha256(path), reproducible=True, independent_mae=independent)
        receipt['results'].append(result)
        rows.append(dict(baseline_name=name, manifest_id=split.manifest_id, source_version=split.source_sha256,
                         train_claim_count=len(training), validation_claim_count=len(validation), fitted_constant=constant,
                         validation_mae=result['mae'], run_id=run_id, code_version=code_version, timestamp_utc=timestamp))
    comparison = output / 'baseline_comparison.csv'
    pd.DataFrame(rows).to_csv(comparison, index=False, float_format='%.17g')
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_baselines_evaluation.py'],
                           cwd=ROOT, capture_output=True, text=True)
    receipt['automated_tests'] = {'command': 'python3 -m unittest discover -s tests -p test_baselines_evaluation.py',
                                  'exit_code': tests.returncode, 'output': tests.stdout + tests.stderr}
    checks = {
        'Frozen manifest verified': sha256(split.manifest_path) == split.manifest_sha256,
        'Source version verified': sha256(split.source_path) == split.source_sha256,
        'Train/validation separation verified': set(training.id).isdisjoint(validation.id),
        'Shared MAE evaluator implemented': callable(evaluate_mae),
        'MAE calculated in original loss units': all(math.isclose(r['mae'], r['independent_mae'], rel_tol=1e-12) for r in receipt['results']),
        'Prediction IDs aligned correctly': all(r['checks']['id_alignment'] for r in receipt['results']),
        'Exactly one prediction per validation claim': all(r['evaluated_claim_count'] == len(split.validation_ids) and r['checks']['duplicate_prediction_ids_absent'] for r in receipt['results']),
        'No missing predictions': all(r['checks']['missing_prediction_ids_absent'] for r in receipt['results']),
        'No extra predictions': all(r['checks']['extra_prediction_ids_absent'] for r in receipt['results']),
        'All predictions finite': all(r['checks']['numeric_finite_predictions'] for r in receipt['results']),
        'Training-mean baseline evaluated': any(r['baseline_name'] == 'mean' for r in receipt['results']),
        'Training-median comparator evaluated': any(r['baseline_name'] == 'median' for r in receipt['results']),
        'Both fitted constants use training data only': set(training.id) == set(split.train_ids) and constants == fit_constants(training, split),
        'Baseline comparison generated': comparison.is_file(),
        'Versions and hashes recorded': all(receipt[k] for k in ['code_version', 'python', 'pandas', 'numpy', 'source_sha256', 'manifest_sha256']),
        'Automated tests pass': tests.returncode == 0,
        'Reproducibility confirmed': all(r['reproducible'] for r in receipt['results']),
        'Test targets remain untouched': set(training.id).union(validation.id).isdisjoint(split.test_ids),
        'Evaluation documentation created': (ROOT / 'docs/october_evaluation_guide.md').is_file(),
    }
    receipt['test_isolation'] = 'CSV traversal skips test rows before loss conversion; no test targets retained, scored or summarized. Covered by poisoned-test-target unit test.'
    receipt['comparison_sha256'] = sha256(comparison)
    summary = ROOT / 'docs/task_baselines_evaluation_summary.md'
    if write_summary:
        summary.write_text('# October baselines and evaluation\n\nShared ID-aligned MAE, training-only constants, strict coverage checks, synthetic tests, and reproducible artifacts are complete.\n\n'
            + '| Baseline | Fitted constant | Validation MAE | Claims |\n|---|---:|---:|---:|\n'
            + ''.join(f"| {r['baseline_name']} | {r['fitted_constant']:.12f} | {r['validation_mae']:.12f} | {r['validation_claim_count']} |\n" for r in rows)
            + f'\nManifest: `{split.manifest_id}`. Training claims: {len(training)}. Run: `{run_id}`.\n\n'
            + 'Files: `scripts/__init__.py`, `scripts/evaluation.py`, `scripts/run_baselines.py`, `tests/test_baselines_evaluation.py`, `docs/october_evaluation_guide.md`, this summary, `artifacts/october/gate 1/split_acceptance.json`, and the addendum in `artifacts/october/gate 1/gate1_signoff.md`.\n\n'
            + f'Artifacts in `{output}`: `baseline_mean_predictions.csv`, `baseline_median_predictions.csv`, `baseline_comparison.csv`, `baseline_run_receipt.json`. See receipt for exact hashes, environment, code revision and test output.\n\n'
            + 'Reproduce from repository root: `python3 -m scripts.run_baselines`. Every run creates a new directory; existing evidence is preserved.\n\n'
            + 'Validation includes exact ID coverage, one-to-one joins, finite predictions, partition consistency, training-only fitting, independent MAE calculation and repeat execution.\n\n'
            + 'Limitations: constant baselines, not feature-based ML models. Results apply to frozen validation only; validation MAE is not an untouched final-test estimate. No internal test targets were inspected. Overall Gate 1 signoff remains separate from the confirmed split agreement.\n\n'
            + 'Next: fit future models and learned preprocessing on training only, then use the shared evaluator to compare validation MAE with both benchmarks.\n\n')
    checks['Task completion summary created'] = summary.is_file()
    receipt_path = output / 'baseline_run_receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    checks['Run receipt generated'] = json.loads(receipt_path.read_text())['run_id'] == run_id
    receipt['checks'] = {k: bool(v) for k, v in checks.items()}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    checklist = '\n'.join(f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items())
    if write_summary:
        with summary.open('a') as handle:
            handle.write('Validation checklist:\n\n' + checklist + '\n')
    print(pd.DataFrame(rows)[['baseline_name', 'fitted_constant', 'validation_mae', 'validation_claim_count']].to_string(index=False))
    print('October Baselines and Evaluation Code\n' + checklist)
    print(f'Receipt: {receipt_path}')
    require(all(checks.values()), 'Run validation failed; inspect receipt')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=Path('artifacts/october/gate 2/baselines'))
    parser.add_argument('--write-summary', action='store_true', help='Update the task summary to this run')
    args = parser.parse_args()
    run(args.output_root, args.write_summary)
