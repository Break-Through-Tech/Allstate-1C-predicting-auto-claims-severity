"""Independently recompute saved real-run MAEs; never fit or read test targets."""
import argparse
import json
import math
from pathlib import Path
import statistics

import pandas as pd

from scripts import run_xgboost as r
from scripts.evaluation import (checked_frame, claim_ids, evaluate_mae, evaluate_training_mae,
                                load_frozen_split, load_partition_targets)


def close(actual, expected, label):
    r.require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9), f'{label}: {actual} != {expected}')


def independent_mae(truth, predictions):
    values = truth.set_index('id').loss
    predicted = predictions.set_index('id').prediction
    r.require(values.index.is_unique and predicted.index.is_unique
              and set(values.index) == set(predicted.index), 'Independent metric ID mismatch')
    return math.fsum(abs(float(values.loc[i]) - float(predicted.loc[i])) for i in values.index) / len(values)


def predictions(path, ids):
    frame = pd.read_csv(path, dtype={'id': 'string'}, float_precision='round_trip')
    return checked_frame(frame, 'prediction', ids, str(path))


def run(output):
    campaign = r.ROOT / r.CAMPAIGN
    receipt = json.loads((campaign / 'run_receipt.json').read_text())
    r.require(receipt['status'] == receipt['stage'] == 'COMPLETE' and receipt['synthetic'] is False,
              'Only a completed real campaign can be audited')
    r.require(receipt['cv_fits_attempted'] == 30 and receipt['configurations_attempted'] == 6,
              'Real experiment budget mismatch')
    r.require(len(receipt['results']) == 6 and set(receipt['releases']) == {'initial', 'final'}, 'Incomplete experiment')
    r.require(receipt['code_sha256'] == r.code_hashes(), 'Fitting code changed during the run')
    r.require(all(x['status'] == 'PASS' for x in receipt['stage_history']) and len(receipt['stage_history']) == 5,
              'Failed, interrupted or missing stage')
    r.require(all(x['environment'] == receipt['environment'] for x in receipt['stage_history']), 'Stage environment drift')
    r.require(r.sha256(r.ROOT / r.CONFIG) == receipt['config_sha256'], 'Config changed during run')
    split = load_frozen_split()
    training, validation = load_partition_targets(split)  # Skips test before loss conversion.
    config = receipt['config']
    fold_path = r.ROOT / config['inputs']['cv_folds']
    r.require(r.sha256(fold_path) == config['inputs']['cv_folds_sha256'], 'Saved fold hash mismatch')
    folds = r.verify_folds(pd.read_csv(fold_path), split)
    r.require(receipt['frozen_inputs'] == {'source_sha256': split.source_sha256,
              'manifest_sha256': split.manifest_sha256, 'cv_folds_sha256': r.sha256(fold_path),
              'training_claims': len(training)}, 'Receipt source/split/fold identities differ')
    rows = []
    for item in receipt['results']:
        r.require(item['status'] == 'PASS' and len(item['fold_results']) == 5, 'Invalid CV result')
        path = campaign / f"{item['id']}_oof.csv"
        r.require(r.sha256(path) == item['prediction_sha256'], 'OOF artifact hash mismatch')
        frame = pd.read_csv(path, dtype={'id': 'string'}, float_precision='round_trip')
        r.require(list(frame.columns) == ['id', 'prediction', 'fold'], 'Unexpected OOF schema')
        frame['id'] = claim_ids(frame.id, 'OOF')
        pred = checked_frame(frame[['id', 'prediction']], 'prediction', split.train_ids, 'OOF')
        r.require(frame.set_index('id').sort_index().fold.equals(folds.fold), 'OOF fold assignments changed')
        pooled = independent_mae(training, pred)
        close(pooled, item['pooled_oof_mae'], 'pooled OOF')
        close(pooled, evaluate_training_mae(training, pred, split=split, held_out_ids=split.train_ids)['mae'], 'shared OOF')
        values = []
        for fold in item['fold_results']:
            ids = folds.index[folds.fold.eq(fold['fold'])]
            truth = training.loc[training.id.isin(ids)]
            subset = pred.loc[pred.id.isin(ids)]
            r.require(len(subset) == fold['claims'], 'Fold support mismatch')
            mae = independent_mae(truth, subset)
            close(mae, fold['mae'], 'fold MAE')
            values.append(mae)
        close(statistics.mean(values), item['fold_mean_mae'], 'fold mean')
        close(statistics.stdev(values), item['fold_sample_sd'], 'fold sample SD')
        r.require(int((pred.prediction < 0).sum()) == item['negative_prediction_count'], 'Negative count mismatch')
        rows.append({'candidate': item['id'], 'max_depth': item['parameters']['max_depth'],
                     'learning_rate': item['parameters']['learning_rate'], 'pooled_oof_mae': pooled,
                     'fold_mean_mae': statistics.mean(values), 'fold_sample_sd': statistics.stdev(values),
                     'runtime_seconds': item['runtime_seconds']})
    initial = receipt['results'][:5]
    minimum = min(x['pooled_oof_mae'] for x in initial)
    selected = min([x for x in initial if x['pooled_oof_mae'] <= minimum + 1],
                   key=lambda x: (x['parameters']['max_depth'], x['parameters']['n_estimators'],
                                  x['parameters']['learning_rate'], x['runtime_seconds']))
    r.require(selected['id'] == receipt['initial_winner'], 'Initial tie-rule selection mismatch')
    after = receipt['results'][-1]
    changed = [key for key in selected['parameters'] if selected['parameters'][key] != after['parameters'][key]]
    r.require(changed == ['max_depth'], 'Follow-up did not change exactly tree depth')
    r.require(after['parameters']['max_depth'] not in {x['parameters']['max_depth'] for x in initial}, 'Depth already tested')
    plan = json.loads((campaign / 'followup_plan.json').read_text())
    r.require(r.sha256(campaign / 'followup_plan.json') == receipt['followup_plan_sha256']
              and plan['frozen_utc'] < after['started_utc'] and plan['rationale'].strip(), 'Follow-up was not frozen first')
    improvement = rows[next(i for i, x in enumerate(rows) if x['candidate'] == selected['id'])]['pooled_oof_mae'] - rows[-1]['pooled_oof_mae']
    threshold = receipt['readiness']['minimum_mae_improvement']
    close(improvement, receipt['comparison']['improvement'], 'keep improvement')
    r.require(threshold == 1.0 and receipt['comparison']['keep_followup'] == (improvement >= threshold), 'Keep rule mismatch')
    r.require(receipt['final_candidate'] == (after['id'] if improvement >= threshold else selected['id']), 'Retained candidate mismatch')
    scores = {}
    for label, item in receipt['releases'].items():
        r.require(item['status'] == 'PASS' and item['model_round_trip'], 'Invalid final model')
        for filename, digest in item['artifact_sha256'].items():
            r.require(r.sha256(campaign / filename) == digest, 'Release artifact hash mismatch')
        pred = predictions(campaign / f'{label}_validation_predictions.csv', split.validation_ids)
        mae = independent_mae(validation, pred)
        close(mae, item['validation_mae'], 'saved validation MAE')
        close(mae, evaluate_mae(validation, pred, split=split)['mae'], 'shared validation MAE')
        r.require(item['candidate_id'] == (selected['id'] if label == 'initial' else after['id']), 'Wrong released candidate')
        scores[label] = mae
    baselines = r.ROOT / 'artifacts/october/gate 2/baselines/baselines-20261025T034742Z-0e9ea822'
    baseline_receipt = json.loads((baselines / 'baseline_run_receipt.json').read_text())
    comparison = []
    for name in ['mean', 'median']:
        item = next(x for x in baseline_receipt['results'] if x['baseline_name'] == name)
        path = baselines / f'baseline_{name}_predictions.csv'
        r.require(r.sha256(path) == item['prediction_sha256'], 'Baseline prediction hash mismatch')
        score = independent_mae(validation, predictions(path, split.validation_ids))
        close(score, item['mae'], 'baseline MAE')
        comparison.append({'model': f'training_{name}_baseline', 'validation_mae': score})
    glm = r.ROOT / 'artifacts/october/gate 3/comparison_inputs/glm-20261103T055706Z-0748a4b5'
    glm_receipt = json.loads((glm / 'run_receipt.json').read_text())
    r.require(glm_receipt['manifest_sha256'] == split.manifest_sha256 and glm_receipt['source_sha256'] == split.source_sha256,
              'GLM comparison uses different source/split')
    r.require(r.sha256(glm / 'validation_predictions.csv') == glm_receipt['prediction_sha256'], 'GLM prediction hash mismatch')
    glm_score = independent_mae(validation, predictions(glm / 'validation_predictions.csv', split.validation_ids))
    close(glm_score, glm_receipt['validation']['mae'], 'GLM MAE')
    comparison.extend([{'model': 'frozen_glm', 'validation_mae': glm_score},
                       {'model': 'xgboost_initial', 'validation_mae': scores['initial']},
                       {'model': 'xgboost_followup', 'validation_mae': scores['final']}])
    execution = r.ROOT / 'artifacts/october/gate 3/xgboost_execution_20261112'
    controller = json.loads((execution / 'automation_receipt.json').read_text())
    recommendation = json.loads((execution / 'depth_recommendation.json').read_text())
    r.require(controller['status'] == 'COMPLETE' and controller['first_real_fit_verified'], 'Controller did not complete')
    r.require(r.sha256(execution / 'depth_recommendation.json') == controller['depth_recommendation_sha256'], 'Recommendation changed')
    r.require(recommendation['frozen_before_validation_utc'] < receipt['releases']['initial']['started_utc']
              and recommendation['value'] == after['parameters']['max_depth']
              and recommendation['rationale'] == plan['rationale'], 'Depth was not fixed from CV before validation')
    audit = {'status': 'PASS', 'audited_utc': r.now(), 'training_commit': receipt['git_commit'],
             'auditor_sha256': r.sha256(Path(__file__)), 'campaign_receipt_sha256': r.sha256(campaign / 'run_receipt.json'),
             'source_sha256': split.source_sha256, 'manifest_sha256': split.manifest_sha256,
             'training_claims': len(training), 'validation_claims': len(validation),
             'cv_fits': 30, 'configurations': 6, 'full_training_refits': 2, 'failed_attempts': 0,
             'before_id': selected['id'], 'after_id': after['id'], 'changed_settings': changed,
             'before_oof_mae': selected['pooled_oof_mae'], 'after_oof_mae': after['pooled_oof_mae'],
             'oof_improvement': improvement, 'minimum_mae_improvement': threshold, 'keep_followup': improvement >= threshold,
             'retained_candidate': receipt['final_candidate'],
             'retained_model_artifact': str((campaign / ('final_model.json' if improvement >= threshold else 'initial_model.json')).relative_to(r.ROOT)),
             'retained_preprocessing_artifact': str((campaign / ('final_preprocessing.json' if improvement >= threshold else 'initial_preprocessing.json')).relative_to(r.ROOT)),
             'before_validation_mae': scores['initial'], 'after_validation_mae': scores['final'],
             'fit_runtime_seconds': receipt['fit_runtime_seconds'], 'elapsed_seconds': controller['elapsed_seconds'],
             'selection_uses_training_only': True, 'all_saved_scores_independently_match': True,
             'test_partition': 'Skipped before loss conversion; never fitted, tuned, predicted or evaluated',
             'verification_validation_access': 'Rescored only existing saved predictions for independent verification/comparison; no additional model fits or candidates.'}
    output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(rows).to_csv(output / 'cv_results.csv', index=False, float_format='%.17g')
    pd.DataFrame(comparison).to_csv(output / 'model_comparison.csv', index=False, float_format='%.17g')
    r.write_json(output / 'results_audit.json', audit, new=True)
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
