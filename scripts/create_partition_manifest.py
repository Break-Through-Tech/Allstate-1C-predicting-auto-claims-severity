"""Reproduce the October proposal without training models or profiling test targets.

Run from any directory: python3 scripts/create_partition_manifest.py
Existing different artifacts are never overwritten. Use a new --output-dir for
an approved new version. No seed search or configurable proportions are exposed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEPTEMBER = ROOT / 'artifacts/september'
OUTPUT = ROOT / 'artifacts/october/gate 1'
CATS = [f'cat{i}' for i in range(1, 117)]
CONTS = [f'cont{i}' for i in range(1, 15)]
FIELDS = ['id', *CATS, *CONTS, 'loss']
VERSION = 'october-split-v1'
SEED = 42
WEIGHTS = {'train': 75, 'validation': 15, 'test': 10}
METHOD = 'SHA-256 seeded pseudorandom ranking of canonical claim IDs'
ELIGIBILITY_RULES = [
    'Exact authoritative source SHA-256, byte count, row count and ordered schema.',
    'All required source fields present; dictionary v1.1.0 source roles verified.',
    'Every id is a nonmissing canonical positive integer and unique, matching source int64 identity.',
    'Every loss passes numeric, finite and strictly-positive eligibility checks before assignment.',
    'No exclusions for high loss, rare labels, cardinality or predictor values; any integrity violation aborts the whole run.',
]
TEST_POLICY = (
    'Reserved for final evaluation after team approval and model-selection procedure freeze. '
    'Only test membership and row count are exported. No test target statistics, plots, '
    'high-loss counts, target-informed assignment or test predictor diagnostics are computed. '
    'Before assignment, the entire source receives only mandatory loss-validity predicates; '
    'no per-test values or aggregates are exposed. September previously examined the full file.'
)


class IntegrityError(ValueError):
    """A failed prerequisite; the eligible population must not be silently repaired."""


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def csv_bytes(frame):
    return frame.to_csv(index=False, lineterminator='\n', float_format='%.12g').encode()


def canonical_id(value):
    require(isinstance(value, str) and re.fullmatch(r'[1-9][0-9]*', value) is not None,
            'Invalid id format; expected canonical positive integer. No rows excluded.')
    number = int(value)
    require(number <= np.iinfo(np.int64).max, 'Identifier outside source int64 range.')
    return number


def verified_reference(manifest, filename):
    # The October repository migration moved files without updating historical paths.
    entries = [e for e in manifest['files'] if Path(e['path']).name == filename]
    require(len(entries) == 1, f'Missing/ambiguous September manifest entry: {filename}')
    path = SEPTEMBER / filename
    require(sha256(path) == entries[0]['sha256'], f'September reference hash mismatch: {filename}')
    return path


def load_and_verify_source():
    manifest_path = SEPTEMBER / 'artifact_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    source = ROOT / manifest['source']['path']
    require(sha256(source) == manifest['source']['sha256'], 'Source SHA-256 mismatch; stopping before assignment.')
    require(source.stat().st_size == manifest['source']['bytes'], 'Source byte count mismatch.')
    with source.open(newline='') as handle:
        header = next(csv.reader(handle))
    require(header == FIELDS, 'Source ordered schema differs from frozen field roles.')
    require(len(header) == manifest['source']['columns'], 'Source column count mismatch.')
    profile_path = verified_reference(manifest, 'source_profile.csv')
    dictionary_path = verified_reference(manifest, 'data_dictionary_v1.1.0.csv')
    profile = pd.read_csv(profile_path, keep_default_na=False)
    dictionary = pd.read_csv(dictionary_path, keep_default_na=False)
    source_roles = dictionary.loc[dictionary.field_type.eq('source')]
    require(source_roles.field.is_unique and set(source_roles.field) == set(FIELDS), 'Dictionary source fields differ.')
    require(profile.column_name.is_unique and set(profile.column_name) == set(FIELDS), 'Source profile fields differ.')
    require(source_roles.version.eq('v1.1.0').all(), 'Unexpected source-role version.')
    expected_roles = {'id': 'identifier', 'loss': 'target',
                      **dict.fromkeys(CATS, 'categorical predictor'),
                      **dict.fromkeys(CONTS, 'continuous predictor')}
    require(source_roles.set_index('field').role.to_dict() == expected_roles, 'Dictionary field roles differ.')
    expected_profile = {'id': 'identifier', 'loss': 'regression_target',
                        **dict.fromkeys(CATS, 'categorical_predictor'),
                        **dict.fromkeys(CONTS, 'continuous_predictor')}
    require(profile.set_index('column_name').role.to_dict() == expected_profile, 'Profile field roles differ.')
    require(int(profile.set_index('column_name').loc['id', 'unique_count']) == manifest['source']['rows'],
            'Source profile population differs from manifest.')
    return source, manifest


def check_eligibility(source, expected_rows):
    """Global validity only, before assignment; discard loss after predicates.

    No target values, quantiles or partition-specific target summaries are logged.
    Counts of invalid rows are actionable integrity errors, never automatic exclusions.
    """
    ids = []
    invalid_loss = 0
    with Path(source).open(newline='') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == FIELDS, 'Eligibility source schema mismatch.')
        for row in reader:
            require(None not in row and all(row[c] is not None for c in FIELDS), 'Malformed source row.')
            ids.append(canonical_id(row['id']))
            try:
                value = float(row['loss'])
                valid = bool(np.isfinite(value) and value > 0)
            except (TypeError, ValueError):
                valid = False
            invalid_loss += not valid
    require(len(ids) == expected_rows, 'Source row count mismatch; no population changes allowed.')
    require(len(set(ids)) == len(ids), 'Duplicate IDs found; no rows silently dropped.')
    require(invalid_loss == 0, f'Eligibility failed: {invalid_loss} rows have invalid loss; stop, no exclusions made.')
    summary = {'source_rows': len(ids), 'included_rows': len(ids), 'excluded_rows': 0,
               'exclusion_reasons': [], 'policy': 'all-or-abort', 'rules': ELIGIBILITY_RULES,
               'invalid_id_count': 0, 'duplicate_id_count': 0, 'invalid_loss_count': invalid_loss}
    return ids, summary


def partition_counts(n):
    """Largest-remainder allocation; ties use declared partition order."""
    require(n >= 10, 'Population too small for three partitions.')
    counts = {p: n * w // 100 for p, w in WEIGHTS.items()}
    order = sorted(WEIGHTS, key=lambda p: -(n * WEIGHTS[p] % 100))
    for p in order[:n - sum(counts.values())]:
        counts[p] += 1
    return counts


def assign_partitions(ids, seed=SEED):
    require(len(ids) == len(set(ids)), 'Cannot split duplicate IDs.')
    require(all(isinstance(i, (int, np.integer)) and i > 0 for i in ids), 'Canonical integer IDs required.')
    ordered = sorted(ids)
    # No targets/predictors enter this deterministic pseudo-random ordering.
    ranked = sorted(ordered, key=lambda i: (
        hashlib.sha256(f'{VERSION}|{seed}|{i}'.encode('ascii')).digest(), i))
    counts = partition_counts(len(ids))
    assigned = {}
    start = 0
    for label, count in counts.items():
        for i in ranked[start:start + count]:
            assigned[i] = label
        start += count
    return pd.DataFrame({'id': ordered, 'partition': [assigned[i] for i in ordered]})


def validate_manifest(frame, eligible_ids):
    require(list(frame.columns) == ['id', 'partition'], 'Manifest must expose only id and partition.')
    require(frame.id.notna().all() and frame.id.is_unique, 'Manifest ID missing or duplicated/overlapping.')
    require(set(frame.id) == set(eligible_ids), 'Manifest has omitted, ineligible or unknown IDs.')
    require(len(frame) == len(eligible_ids), 'Manifest row count mismatch.')
    require(set(frame.partition) == set(WEIGHTS), 'Unexpected/missing partition labels.')
    expected = partition_counts(len(eligible_ids))
    require(frame.partition.value_counts().to_dict() == expected, 'Partition counts differ from allocation.')
    require(all(abs(expected[p] - len(eligible_ids) * w / 100) < 1 for p, w in WEIGHTS.items()),
            'Partition proportions outside rounding tolerance.')
    return expected


def load_development_rows(source, manifest):
    """Filter by ID BEFORE converting or retaining loss/predictors; test rows skipped."""
    wanted = manifest.loc[manifest.partition.isin(['train', 'validation'])].set_index('id').partition.to_dict()
    records = []
    with Path(source).open(newline='') as handle:
        for row in csv.DictReader(handle):
            i = canonical_id(row['id'])
            if i not in wanted:
                continue  # Do not parse test loss or retain test predictor values.
            records.append({'id': i, 'partition': wanted[i], 'loss': float(row['loss']),
                            **{c: row[c] for c in CATS}})
    development = pd.DataFrame(records)
    require(development.id.is_unique and set(development.id) == set(wanted), 'Development join is not one-to-one.')
    require(set(development.partition) == {'train', 'validation'}, 'Test row entered diagnostics.')
    return development


def generate_diagnostics(manifest, development, threshold, rare_threshold):
    require(set(development.partition) == {'train', 'validation'}, 'Diagnostic input contains test/unknown partition.')
    expected_ids = set(manifest.loc[manifest.partition.ne('test'), 'id'])
    require(set(development.id) == expected_ids and development.id.is_unique, 'Diagnostic IDs do not match development partitions.')
    assignments = manifest.set_index('id').partition
    require(development.partition.eq(development.id.map(assignments)).all(), 'Diagnostic partition mislabeling.')
    require(np.isfinite(development.loss).all() and development.loss.gt(0).all(), 'Invalid development loss.')
    rows = []
    def add(partition, metric, value, denominator, unit):
        rows.append(dict(partition=partition, metric=metric, value=value, denominator=denominator, unit=unit))
    for label in WEIGHTS:
        count = int(manifest.partition.eq(label).sum())
        add(label, 'row_count', count, len(manifest), 'claims')
        add(label, 'share_of_eligible', count / len(manifest), len(manifest), 'share')
    for label in ['train', 'validation']:
        y = development.loc[development.partition.eq(label), 'loss']
        metrics = {'loss_count': len(y), 'loss_mean': y.mean(), 'loss_median': y.median(),
                   'loss_std_ddof1': y.std(ddof=1), 'loss_p90': y.quantile(.90),
                   'loss_p95': y.quantile(.95), 'loss_p99': y.quantile(.99), 'loss_max': y.max()}
        for metric, value in metrics.items():
            add(label, metric, value, len(y), 'claims' if metric == 'loss_count' else 'original loss units')
        add(label, 'historical_september_p95_threshold', threshold, len(y), 'original loss units')
        add(label, 'high_loss_count', int(y.gt(threshold).sum()), len(y), 'claims')
        add(label, 'high_loss_share', float(y.gt(threshold).mean()), len(y), 'share')
    training = development.loc[development.partition.eq('train')]
    validation = development.loc[development.partition.eq('validation')]
    coverage = []
    for feature in CATS:
        require(training[feature].notna().all() and validation[feature].notna().all(), 'Missing categorical value.')
        tc = training[feature].value_counts()
        vc = validation[feature].value_counts()
        unseen = sorted(set(vc.index) - set(tc.index))
        unseen_count = int(vc.reindex(unseen, fill_value=0).sum())
        train_rare = tc.loc[tc.lt(rare_threshold)]
        validation_rare = vc.loc[vc.lt(rare_threshold)]
        on_train_rare = int(validation[feature].isin(train_rare.index).sum())
        coverage.append(dict(
            feature=feature, training_cardinality=len(tc), validation_cardinality=len(vc),
            validation_unseen_level_count=len(unseen), validation_unseen_levels=json.dumps(unseen),
            validation_unseen_observation_count=unseen_count, validation_denominator=len(validation),
            validation_unseen_observation_share=unseen_count / len(validation),
            eda_rare_support_threshold=rare_threshold, training_denominator=len(training),
            training_rare_level_count=len(train_rare), training_rare_observation_count=int(train_rare.sum()),
            training_rare_observation_share=float(train_rare.sum() / len(training)),
            validation_local_rare_level_count=len(validation_rare),
            validation_local_rare_observation_count=int(validation_rare.sum()),
            validation_local_rare_observation_share=float(validation_rare.sum() / len(validation)),
            validation_observations_on_training_rare_levels=on_train_rare,
            validation_share_on_training_rare_levels=on_train_rare / len(validation)))
    diagnostics = pd.DataFrame(rows)
    coverage = pd.DataFrame(coverage)
    require(set(diagnostics.loc[diagnostics.partition.eq('test'), 'metric']) == {'row_count', 'share_of_eligible'},
            'Test target diagnostics prohibited.')
    require(len(coverage) == 116 and set(coverage.feature) == set(CATS), 'Incomplete categorical coverage.')
    return diagnostics, coverage


def export_artifacts(output, payloads):
    """Preflight every file before any write; identical reruns are no-ops."""
    output = Path(output)
    for name, content in payloads.items():
        path = output / name
        require(not path.exists() or path.read_bytes() == content,
                f'Refusing to overwrite different existing artifact: {path}. Use a new versioned output directory.')
    output.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        path = output / name
        if not path.exists():
            path.write_bytes(content)
        require(path.read_bytes() == content, f'Export verification failed: {name}')


def run(output=OUTPUT):
    source, reference = load_and_verify_source()
    source_sha = sha256(source)
    ids, eligibility = check_eligibility(source, reference['source']['rows'])
    manifest = assign_partitions(ids)
    counts = validate_manifest(manifest, ids)
    manifest_bytes = csv_bytes(manifest)
    repeat_ok = manifest_bytes == csv_bytes(assign_partitions(ids))
    order_ok = manifest_bytes == csv_bytes(assign_partitions(list(reversed(ids))))
    require(repeat_ok and order_ok, 'Assignment reproducibility failed.')
    threshold_path = verified_reference(reference, 'target_summary.csv')
    target_reference = pd.read_csv(threshold_path).set_index('metric')
    threshold = float(target_reference.loc['p95', 'value'])
    cat_reference_path = verified_reference(reference, 'categorical_inventory.csv')
    cat_reference = pd.read_csv(cat_reference_path)
    rare_rules = cat_reference.rare_level_threshold.unique()
    require(len(rare_rules) == 1, 'Ambiguous inherited rare-level threshold.')
    rare_threshold = int(rare_rules[0])
    development = load_development_rows(source, manifest)
    diagnostics, coverage = generate_diagnostics(manifest, development, threshold, rare_threshold)
    require(sha256(source) == source_sha, 'Source changed during run.')
    design = (ROOT / 'docs/october_split_design.md').read_text()
    has = lambda *terms: all(term in design for term in terms)
    checks = {
        'Authoritative source verified': sha256(source) == reference['source']['sha256'],
        'Field roles verified': len(FIELDS) == reference['source']['columns'],
        'Split design documented': has(METHOD, 'PROPOSED', VERSION),
        'Proportions documented': has('75%', '15%', '10%'),
        'Seed documented': has('seed 42'),
        'Eligibility rules documented': has('unique', 'finite', 'strictly positive', 'all-or-abort'),
        'Internal test decision documented': has('sealed', 'final evaluation'),
        'Every eligible claim assigned exactly once': manifest.id.is_unique and len(manifest) == len(ids),
        'No partition overlap': manifest.id.is_unique,
        'No omitted eligible claims': set(manifest.id) == set(ids),
        'Partition counts reconcile': counts == partition_counts(len(ids)) and sum(counts.values()) == len(ids),
        'Reproducibility confirmed': repeat_ok and order_ok,
        'Train/validation target summaries generated': len(diagnostics.loc[diagnostics.metric.str.startswith('loss_')]) == 16,
        'High-loss support documented': has('historical', 'p95') and diagnostics.metric.eq('high_loss_count').sum() == 2,
        'Categorical coverage documented': coverage.feature.is_unique and set(coverage.feature) == set(CATS),
        'Test targets remain uninspected': set(development.id).isdisjoint(manifest.loc[manifest.partition.eq('test'), 'id'])
            and set(diagnostics.loc[diagnostics.partition.eq('test'), 'metric']) == {'row_count', 'share_of_eligible'},
        'Split-change criteria documented': has('Predeclared Criteria for Changing the Split', 'approve', 'new version'),
        'Source dataset unchanged': sha256(source) == source_sha,
    }
    print('October Split Design and Manifest')
    for label, passed in checks.items():
        print(f"{label}: {'PASS' if passed else 'FAIL'}")
    require(all(checks.values()), 'Checklist failed; no artifacts exported.')
    config = {'version': VERSION, 'method': METHOD, 'seed': SEED, 'proportions_percent': WEIGHTS,
              'ranking_key': 'SHA256(ASCII("october-split-v1|42|<canonical integer id>")); ties by integer id',
              'rounding': 'largest remainder; fractional ties in train,validation,test order',
              'manifest_order': 'ascending integer id', 'status': 'PROPOSED; team/advisor confirmation pending'}
    payloads = {'october_partition_manifest.csv': manifest_bytes,
                'october_split_diagnostics.csv': csv_bytes(diagnostics),
                'october_categorical_coverage.csv': csv_bytes(coverage)}
    code_rel = 'scripts/create_partition_manifest.py'
    # Content-addressed code is authoritative; last commit touching the source file
    # is intentionally not used because it changes when generated files are committed.
    metadata = {
        'split': config,
        'source': {**reference['source'], 'manifest_path': 'artifacts/september/artifact_manifest.json',
                   'manifest_sha256': sha256(SEPTEMBER / 'artifact_manifest.json')},
        'eligibility': eligibility, 'eligible_row_count': len(ids),
        'field_roles': {'path': 'artifacts/september/data_dictionary_v1.1.0.csv', 'version': 'v1.1.0',
                        'sha256': sha256(SEPTEMBER / 'data_dictionary_v1.1.0.csv'),
                        'identifier': 'id', 'categorical_predictors': CATS, 'continuous_predictors': CONTS,
                        'target': 'loss', 'id_is_predictor': False, 'target_units': 'original loss units'},
        'partition_counts': counts, 'test_policy': TEST_POLICY,
        'high_loss_definition': {'comparison': 'loss > archived September p95', 'threshold': threshold,
                                 'reference': 'artifacts/september/target_summary.csv :: p95',
                                 'sha256': sha256(threshold_path), 'scope': 'train/validation diagnostics only; historical full-file EDA exposure'},
        'categorical_support_rule': {'threshold': rare_threshold, 'comparison': 'support < threshold',
                                     'reference': 'artifacts/september/categorical_inventory.csv',
                                     'validation_local_rare': 'descriptive only, not learned preprocessing',
                                     'training_rare': 'observed training levels below threshold; unseen levels reported separately',
                                     'modeling_threshold_selected': False},
        'implementation': {'path': code_rel, 'sha256': sha256(ROOT / code_rel),
                           'configuration_sha256': hashlib.sha256(json_bytes(config)).hexdigest(),
                           'evidence_base_commit': 'd3b6a8b',
                           'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__},
        'artifacts_sha256': {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()},
        'reproducibility': {'same_input_bytes_identical': repeat_ok, 'reversed_id_order_bytes_identical': order_ok},
        'validation': {label: bool(value) for label, value in checks.items()},
    }
    payloads['october_split_metadata.json'] = json_bytes(metadata)
    export_artifacts(output, payloads)
    print('Partition counts:', counts)
    print('Manifest SHA-256:', metadata['artifacts_sha256']['october_partition_manifest.csv'])
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        run(args.output_dir)
    except (IntegrityError, OSError, KeyError, ValueError) as exc:
        print(f'October Split Design and Manifest: FAIL — {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
