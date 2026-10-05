"""Read-only Task #15 documentation checks; no EDA/modeling. Standard library only.

Run: python3 scripts/validate_october_handoff.py
PASS means document coverage/traceability, not human approval or model performance.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def text(path):
    return (ROOT / path).read_text()


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def rows(path):
    with (ROOT / path).open(newline='') as f:
        return list(csv.DictReader(f))


def has(document, *terms):
    return all(term.casefold() in document.casefold() for term in terms)


def section(document, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\n(.*?)(?=^## |\Z)', document, re.M | re.S)
    return match.group(1) if match else ''


def main():
    h = text('docs/october_modeling_handoff.md')
    md = text('docs/october_recommendation_register.md')
    recs = rows('artifacts/october_recommendation_register.csv')
    nb = json.loads(text('notebooks/data-understanding.ipynb'))
    manifest = json.loads(text('artifacts/artifact_manifest.json'))
    overview = text('Challenge-Project-Overview.md')
    summary_cells = [c for c in nb['cells'] if c['cell_type'] == 'markdown'
                     and '# Task #15 Completion Summary' in ''.join(c['source'])]
    summary = ''.join(summary_cells[0]['source']) if len(summary_cells) == 1 else ''
    required = ['recommendation_id', 'recommendation', 'september_evidence', 'evidence_location',
                'rationale', 'recommendation_type', 'october_action', 'validation_needed', 'status']
    schema = bool(recs) and all(set(r) == set(required) and all(r.values()) for r in recs)
    ids = [r.get('recommendation_id', '') for r in recs]
    unique = len(ids) == len(set(ids)) and all(re.fullmatch(r'OCT-REC-\d{3}', x) for x in ids)
    errors = []
    mirror = schema
    for r in recs:
        if not schema:
            break
        heading = f"## {r['recommendation_id']} — {r['recommendation']}"
        match = re.search(re.escape(heading) + r'\n(.*?)(?=\n## |\Z)', md, re.S)
        block = match.group(1) if match else ''
        for key in required[2:]:
            value = r[key]
            if key == 'evidence_location':
                locations = []
                for loc in value.split('; '):
                    path, sep, selector = loc.partition(' :: ')
                    if not sep or not selector.strip() or not (ROOT / path).is_file():
                        errors.append(f"{r['recommendation_id']}: {loc}")
                        continue
                    locations.append(f'[{path}](../{path}) — {selector}')
                    body = text(path)
                    for finding in re.findall(r'(?:FND|HYP)-\d{3}', selector):
                        if finding not in body:
                            errors.append(f'{path}: missing {finding}')
                    if path.endswith('.csv'):
                        headers = next(csv.reader(body.splitlines()))
                        metric_names = {r['metric'] for r in rows(path)} if 'metric' in headers else set()
                        for token in re.findall(r'\b\w+_\w+\b', selector):
                            if token not in headers and token not in metric_names:
                                errors.append(f'{path}: unknown column {token}')
                value = '; '.join(locations)
            mirror &= f'- **{key}:** {value}\n' in block
    for filename, document in [('docs/october_modeling_handoff.md', h),
                               ('docs/october_recommendation_register.md', md),
                               ('notebooks/data-understanding.ipynb', summary)]:
        for target in re.findall(r'\]\(([^)]+)\)', document):
            if '://' in target:
                continue
            path, _, anchor = target.partition('#')
            if not ((ROOT / filename).parent / path).is_file():
                errors.append(f'{filename}: broken link {target}')
            elif anchor == 'task-15-completion-summary' and f'id="{anchor}"' not in summary:
                errors.append(f'{filename}: missing anchor {anchor}')
    frozen = section(h, '2. Frozen Source and Field Roles')
    metric = section(h, '4. Target and Evaluation Metric')
    design = section(h, '5. Proposed Validation Design')
    base = section(h, '6. Baseline Plan')
    leak = section(h, '7. Preprocessing and Leakage Boundaries')
    cat = section(h, '8. Categorical / High-Cardinality Considerations')
    corr = section(h, '9. Correlated-Feature Considerations')
    models = section(h, '10. Candidate Model Families')
    validation = section(h, '11. Required October Validation Evidence')
    questions = section(h, '13. Unresolved Questions for Challenge Advisor')
    deferred = section(h, '14. Work Explicitly Deferred to October')
    code_hash = hashlib.sha256('\n# ---\n'.join(''.join(c['source']) for c in nb['cells']
                                             if c['cell_type'] == 'code').encode()).hexdigest()
    mismatches = [e['path'] for e in manifest['files'] if digest(e['path']) != e['sha256']]
    preserved = (not mismatches and digest(manifest['source']['path']) == manifest['source']['sha256']
                 and code_hash == manifest['code']['code_cells_sha256'])
    t = {r['metric']: float(r['value']) for r in rows('artifacts/target_summary.csv')}
    inventory = rows('artifacts/categorical_inventory.csv')
    rare = rows('artifacts/categorical_low_support_evidence.csv')
    cont = rows('artifacts/continuous_inventory.csv')
    expected = [f"{manifest['source']['rows']:,}", str(manifest['source']['columns']),
                *(f'{t[k]:,.2f}' for k in ['mean', 'p50', 'p95', 'max']), f"{t['skewness']:.3f}",
                str(len(rare)), str(len({r['field_name'] for r in rare})),
                str(sum(int(r['cardinality']) == 2 for r in inventory)),
                str(sum(int(r['cardinality']) <= 4 for r in inventory))]
    expected += [f"{r['column_name']} {r['cardinality']}" for r in
                 sorted(inventory, key=lambda r: int(r['cardinality']), reverse=True)[:3]]
    expected += [f"{r['field']} {float(r['pearson_raw']):.3f}" for r in
                 sorted(cont, key=lambda r: abs(float(r['pearson_raw'])), reverse=True)[:3]]
    outputs = '\n'.join(''.join(o.get('data', {}).get('text/plain', []))
                        for c in nb['cells'] for o in c.get('outputs', []))
    pairs = re.findall(r'^\d+\s+(cont\d+)\s+(cont\d+)\s+([\d.]+)\s+[\d.]+\s*$', outputs, re.M)[:3]
    pair_ok = len(pairs) == 3 and all(f'{a}/{b} {v}' in corr for a, b, v in pairs)
    families = ['generalized linear model (GLM)', 'random forest',
                'gradient boosting machine (GBM)', 'extreme gradient boosting (XGBoost)']
    model_rows = [line for line in models.splitlines() if line.startswith('| ')][2:]
    checks = {
        'Recommendation Register created': schema and unique and mirror,
        'Every recommendation linked to September evidence': schema and not errors,
        'Recommendations labeled as future work': bool(recs) and all(r['status'] == 'PROPOSED' and
            r['recommendation_type'] in {'future_decision', 'proposed_experiment', 'validation_requirement',
                                        'unresolved_question'} for r in recs),
        'Frozen source/roles documented': preserved and has(frozen, manifest['source']['path'],
            manifest['source']['sha256'], 'v1.1.0', 'id', 'NOT an ordinary model feature',
            'cat1', 'cat116', 'cont1', 'cont14', 'nominal', 'Positive continuous regression target'),
        'Original-scale loss + MAE documented': has(metric, 'loss', 'Mean Absolute Error',
            'original `loss` units', 'average absolute difference', 'not a replacement'),
        'Validation design documented': has(design, 'PROPOSED', 'requires October confirmation',
            '5-fold', 'shuffle=True', 'seed 42', 'sample standard deviation', 'pooled', 'training fold', 'group/time'),
        'Mean baseline plan documented': has(base, 'Mean-constant', 'TRAINING-set mean',
            'TRAINING DATA ONLY', 'project explicitly requests', 'No baseline is run'),
        'Median baseline plan documented': has(base, 'Median-constant', 'TRAINING-set median',
            'minimizes absolute error', 'TRAINING DATA ONLY'),
        'Leakage-safe preprocessing documented': has(leak, 'TRAINING', 'Fit preprocessing + transform',
            'VALIDATION', 'TEST/FUTURE', 'Transform only', 'category-frequency', 'rare-category grouping',
            'target-derived transformations', 'imputers', 'scalers', 'feature-selection', 'must not influence fitting', 'pipeline'),
        'High-cardinality handling questions documented': has(cat, 'how should', 'held-out MAE',
            'training-only', 'NOT automatically', 'does not justify feature removal'),
        'Unseen-category handling documented': has(cat, 'unseen', 'inference', 'safe', 'unknown'),
        'Correlated-feature concerns documented': pair_ok and has(corr, 'coefficient interpretation',
            'does not establish', 'held-out original-scale MAE', 'No predictors are removed'),
        'Candidate model families documented': len(model_rows) == 4 and has(overview, *families)
            and has(models, *families, 'candidates', 'not selected', 'Validation required'),
        'Required validation evidence documented': has(validation, 'mean-constant', 'median-constant',
            'original `loss` units', 'split/fold', 'random seed', 'sample counts', 'fold-level MAE', 'mean/std',
            'Training-only', 'did not influence', 'unseen-category', 'configuration', 'code/commit',
            'dependency versions', 'runtime', 'Error distribution', 'high-loss', 'rare/high-cardinality'),
        'Challenge Advisor questions documented': has(questions, 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6',
            'Why it matters', 'Decision affected', 'no inferred answers'),
        'No winning model selected': has(deferred, 'Not Yet Decided', 'Winning model', 'final feature set',
            'final categorical encoder', 'final rare-category threshold', 'final hyperparameters',
            'production-readiness', 'causal interpretation', 'individual claim reserve')
            and has(h, 'No model, baseline, encoder, split, or feature-selection procedure is fitted'),
        'Task completion summary created': len(summary_cells) == 1 and has(summary, 'Work Completed',
            'Files Added or Updated', 'September Evidence Used', 'Key October Recommendations',
            'Modeling Handoff Decisions', 'Proposed / Not Yet Approved', 'Unresolved Questions', 'Validation')
            and all(v in section(h, '3. September Evidence Summary') and v in summary for v in expected),
    }
    print('Task #15 — October Recommendation Register and Modeling Handoff')
    for label, passed in checks.items():
        print(f"{label}: {'PASS' if passed else 'FAIL'}")
    print(f'Unique recommendations: {len(ids)}; CSV/Markdown agreement: {mirror}')
    print('Frozen September source/artifact/code hashes:', 'PASS' if preserved else 'FAIL')
    print('Approval caveat: Gate 3/4 human review and team approval remain pending.')
    for error in errors + mismatches:
        print('FAIL:', error)
    return 0 if all(checks.values()) and preserved else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(f'Task #15 documentation validation: FAIL ({exc})')
        sys.exit(1)
