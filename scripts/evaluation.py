"""Shared original-loss-unit MAE with strict claim-ID and frozen-split checks.

No splitting, fitting, target transformation, clipping, or test scoring occurs here.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
import numbers
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GATE1 = Path('artifacts/october/gate 1')


class EvaluationError(ValueError):
    """Inputs cannot be evaluated completely and unambiguously."""


def require(condition, message):
    if not condition:
        raise EvaluationError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def claim_ids(values, label):
    """Accept integer IDs or canonical decimal strings, never floats/bools/nulls."""
    result = []
    for value in values:
        if isinstance(value, (bool, np.bool_)):
            raise EvaluationError(f'{label}: boolean id is invalid')
        if isinstance(value, numbers.Integral):
            number = int(value)
        elif isinstance(value, str) and re.fullmatch(r'[1-9][0-9]*', value):
            number = int(value)
        else:
            raise EvaluationError(f'{label}: id must be a positive integer or canonical integer string')
        require(0 < number <= np.iinfo(np.int64).max, f'{label}: id outside positive int64 range')
        result.append(number)
    require(len(result) == len(set(result)), f'{label}: duplicate ids')
    return result


def numeric_values(series, label):
    require(pd.api.types.is_numeric_dtype(series.dtype)
            and not pd.api.types.is_bool_dtype(series.dtype)
            and not pd.api.types.is_complex_dtype(series.dtype), f'{label}: values must have a real numeric dtype')
    require(not series.isna().any(), f'{label}: missing values')
    values = series.to_numpy(dtype=np.float64)
    require(np.isfinite(values).all(), f'{label}: all values must be finite')
    return values


def checked_frame(frame, value_column, expected_ids, label):
    require(isinstance(frame, pd.DataFrame), f'{label}: expected a DataFrame')
    require(frame.columns.is_unique and set(frame.columns) == {'id', value_column},
            f'{label}: require exactly id and {value_column} columns')
    require(not frame.empty, f'{label}: empty input')
    ids = claim_ids(frame['id'], label)
    expected = set(expected_ids)
    missing, extra = expected - set(ids), set(ids) - expected
    require(not missing and not extra,
            f'{label}: ID mismatch ({len(missing)} missing, {len(extra)} extra)')
    values = numeric_values(frame[value_column], f'{label}.{value_column}')
    if value_column == 'loss':
        require((values > 0).all(), f'{label}: loss must be strictly positive in original units')
    return pd.DataFrame({'id': ids, value_column: values})


@dataclass(frozen=True)
class FrozenSplit:
    source_path: Path
    source_sha256: str
    manifest_path: Path
    manifest_sha256: str
    manifest_id: str
    train_ids: tuple[int, ...]
    validation_ids: tuple[int, ...]
    test_ids: tuple[int, ...]
    metadata_sha256: str
    acceptance_sha256: str

    def validate(self):
        groups = [claim_ids(ids, name) for ids, name in
                  [(self.train_ids, 'training'), (self.validation_ids, 'validation'), (self.test_ids, 'test')]]
        require(all(groups), 'All frozen partitions must be nonempty')
        require(sum(map(len, groups)) == len(set().union(*map(set, groups))), 'Frozen partitions overlap')
        require(bool(self.manifest_id) and re.fullmatch(r'[0-9a-f]{64}', self.manifest_sha256) is not None,
                'Frozen manifest identity/hash missing or invalid')


def load_frozen_split(root=ROOT):
    """Verify source/reference hashes and ALL source IDs, but read no target values.

    Original proposed metadata is preserved; dated acceptance pins its exact hash.
    """
    root = Path(root)
    metadata_path = root / GATE1 / 'october_split_metadata.json'
    acceptance_path = root / GATE1 / 'split_acceptance.json'
    meta = json.loads(metadata_path.read_text())
    acceptance = json.loads(acceptance_path.read_text())
    source = root / meta['source']['path']
    manifest_path = root / GATE1 / 'october_partition_manifest.csv'
    require(acceptance['status'] == 'accepted_for_baselines', 'Split is not accepted/frozen for baseline work')
    require(acceptance['manifest_id'] == meta['split']['version'], 'Accepted split version differs')
    require(acceptance['manifest_sha256'] == meta['artifacts_sha256'][manifest_path.name]
            == sha256(manifest_path), 'Frozen partition manifest hash mismatch')
    require(acceptance['source_sha256'] == meta['source']['sha256'] == sha256(source), 'Source hash mismatch')
    require(acceptance['partition_counts'] == meta['partition_counts']
            and acceptance['seed'] == meta['split']['seed']
            and acceptance['proportions_percent'] == meta['split']['proportions_percent'], 'Accepted split configuration differs')
    require(source.stat().st_size == meta['source']['bytes'], 'Source byte count mismatch')
    sept_path = root / meta['source']['manifest_path']
    require(sha256(sept_path) == meta['source']['manifest_sha256'], 'September manifest hash mismatch')
    sept = json.loads(sept_path.read_text())
    require(all(meta['source'][k] == sept['source'][k] for k in ['path', 'sha256', 'rows', 'columns', 'bytes']),
            'Source identities disagree between manifests')
    dictionary_path = root / meta['field_roles']['path']
    require(sha256(dictionary_path) == meta['field_roles']['sha256'], 'Field-role dictionary hash mismatch')
    dictionary = pd.read_csv(dictionary_path, keep_default_na=False)
    roles = dictionary.loc[dictionary.field_type.eq('source')]
    expected_roles = {'id': 'identifier', **{f'cat{i}': 'categorical predictor' for i in range(1, 117)},
                      **{f'cont{i}': 'continuous predictor' for i in range(1, 15)}, 'loss': 'target'}
    require(roles.field.is_unique and roles.set_index('field').role.to_dict() == expected_roles
            and roles.version.eq(meta['field_roles']['version']).all(), 'Source field roles/version differ')
    with source.open(newline='') as handle:
        require(next(csv.reader(handle)) == list(expected_roles), 'Source ordered schema mismatch')
    require(len(expected_roles) == meta['source']['columns'], 'Source column count mismatch')
    manifest = pd.read_csv(manifest_path, dtype={'id': 'string', 'partition': 'string'}, keep_default_na=False)
    require(list(manifest.columns) == ['id', 'partition'], 'Unexpected manifest schema')
    ids = claim_ids(manifest.id, 'manifest')
    manifest['id'] = ids
    require(set(manifest.partition) == {'train', 'validation', 'test'}, 'Invalid partition labels')
    require(manifest.partition.value_counts().to_dict() == meta['partition_counts'], 'Frozen partition counts differ')
    # usecols projects id only: no test loss conversion, validation or aggregation.
    source_ids = claim_ids(pd.read_csv(source, usecols=['id'], dtype={'id': 'string'})['id'], 'source')
    require(len(source_ids) == meta['source']['rows'] == meta['eligible_row_count'] == len(ids)
            and set(source_ids) == set(ids), 'Source/manifest population mismatch')
    context = FrozenSplit(source, meta['source']['sha256'], manifest_path, sha256(manifest_path),
                          meta['split']['version'],
                          *(tuple(sorted(manifest.loc[manifest.partition.eq(p), 'id'])) for p in ['train', 'validation', 'test']),
                          sha256(metadata_path), sha256(acceptance_path))
    context.validate()
    return context


def load_partition_targets(split):
    """Read train/validation targets only; skip test rows BEFORE converting loss.

    The shared source CSV bytes are traversed, but no test target is parsed as a
    number, validated, retained, printed or summarized by this task.
    """
    split.validate()
    wanted = set(split.train_ids) | set(split.validation_ids)
    records = []
    with split.source_path.open(newline='') as handle:
        for row in csv.DictReader(handle):
            i = int(row['id'])  # IDs already checked by the source-only projection.
            if i not in wanted:
                continue
            try:
                value = float(row['loss'])
            except (TypeError, ValueError) as exc:
                raise EvaluationError('Non-numeric training/validation loss') from exc
            records.append((i, value))
    targets = pd.DataFrame(records, columns=['id', 'loss'])
    checked_frame(targets, 'loss', wanted, 'development targets')
    training = targets.loc[targets.id.isin(split.train_ids)].copy()
    validation = targets.loc[targets.id.isin(split.validation_ids)].copy()
    return (checked_frame(training, 'loss', split.train_ids, 'training targets').sort_values('id').reset_index(drop=True),
            checked_frame(validation, 'loss', split.validation_ids, 'validation targets').sort_values('id').reset_index(drop=True))


def evaluate_mae(ground_truth, predictions, *, split, run_metadata=None):
    """Return ID-aligned validation MAE and traceability in original loss units.

    Caller must supply original-unit predictions; numeric scale cannot be inferred.
    Negative finite predictions are scored as provided, never silently clipped.
    """
    split.validate()
    truth = checked_frame(ground_truth, 'loss', split.validation_ids, 'ground truth')
    predicted = checked_frame(predictions, 'prediction', split.validation_ids, 'predictions')
    aligned = truth.merge(predicted, on='id', how='inner', validate='one_to_one').sort_values('id')
    require(len(aligned) == len(split.validation_ids), 'Aligned count differs from validation population')
    with np.errstate(over='ignore', invalid='ignore'):
        errors = np.abs(aligned.loss.to_numpy() - aligned.prediction.to_numpy())
        # Divide first to avoid overflowing an otherwise finite average.
        mae = float(np.sum(errors / len(aligned)))
    require(np.isfinite(errors).all() and np.isfinite(mae), 'MAE overflow/non-finite error; cannot report score')
    return {'mae': mae, 'evaluated_claim_count': len(aligned), 'partition': 'validation',
            'partition_id': f'{split.manifest_id}:validation', 'manifest_id': split.manifest_id,
            'manifest_sha256': split.manifest_sha256, 'source_sha256': split.source_sha256,
            'metric': 'MAE', 'units': 'original loss units', 'run_metadata': dict(run_metadata or {}),
            'checks': {'id_alignment': len(aligned) == len(split.validation_ids),
                       'duplicate_prediction_ids_absent': predicted.id.is_unique,
                       'missing_prediction_ids_absent': set(split.validation_ids) <= set(predicted.id),
                       'extra_prediction_ids_absent': set(predicted.id) <= set(split.validation_ids),
                       'numeric_finite_predictions': bool(np.isfinite(predicted.prediction).all())}}
