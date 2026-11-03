"""Fresh-kernel notebook reproduction plus independent Gate 2 transformation checks.

Only an explicitly requested receipt is written. Notebook outputs stay in memory.
No real-target model is trained. The predictor reader never requests loss.
Rachel's notebook is NOT run;
only its LogTargetRegressor definition is loaded for synthetic inverse-rule tests.
"""
import argparse
import ast
from collections import Counter
import math
import os
from pathlib import Path
import pickle
import sys
import types

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scripts.verify_gate2_leng import (
    ROOT, SOURCE, execution_identity, load_json, require,
    sha256_file, verify_frozen_split, write_receipt,
)

NOTEBOOK = ROOT / "notebooks/gate2_preprocessing.ipynb"
TARGET_NOTEBOOK = ROOT / "notebooks/gate2_training_folds.ipynb"
CATS = [f"cat{i}" for i in range(1, 117)]
CONTS = [f"cont{i}" for i in range(1, 15)]
FEATURES = CATS + CONTS


def load_definitions(path, names, module_name, bindings=None):
    """Use actual notebook definitions, without running data loads or writes."""
    notebook = load_json(path)
    source = "\n".join("".join(c["source"]) for c in notebook["cells"]
                       if c["cell_type"] == "code")
    tree = ast.parse(source)
    body = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
            or isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
    found = {n.name for n in body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
    require(found == set(names), f"Notebook definitions missing: {set(names) - found}")
    module = types.ModuleType(module_name)
    module.__dict__.update(bindings or {})
    sys.modules[module_name] = module
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), module.__dict__)
    return module


def reproduce_notebook():
    import nbformat
    from jupyter_client import AsyncKernelManager
    from nbclient import NotebookClient

    source_before = sha256_file(NOTEBOOK)
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    original_sources = [cell.source for cell in notebook.cells]
    code = [c for c in notebook.cells if c.cell_type == "code"]
    require(len(code) == 34, "Recorded notebook no longer has 34 code cells")
    for cell in code:
        cell.outputs = []
        cell.execution_count = None
    class CurrentInterpreterKernel(AsyncKernelManager):
        def format_kernel_cmd(self, extra_arguments=None):
            self.kernel_spec.argv = [
                sys.executable, "-B", "-m", "ipykernel_launcher", "-f", "{connection_file}",
            ]
            return super().format_kernel_cmd(extra_arguments)

    # Let NotebookClient own and clean up its kernel, including failed startup.
    client = NotebookClient(
        notebook, kernel_name="python3", kernel_manager_class=CurrentInterpreterKernel,
        timeout=180, resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute(env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONOPTIMIZE": "0"})
    require([c.execution_count for c in code] == list(range(1, 35)),
            "Notebook did not execute all cells sequentially")
    errors = [o for c in code for o in c.outputs if o.output_type == "error"]
    require(not errors, "Notebook execution errors")
    require(sha256_file(NOTEBOOK) == source_before
            and [cell.source for cell in notebook.cells] == original_sources,
            "Source notebook changed during reproduction")
    print("PASS: All 34 notebook code cells executed in a fresh kernel; zero errors")
    return {"code_cells_executed": 34, "errors": 0,
            "kernel_interpreter": sys.executable, "kernel_optimization": 0,
            "output_blocks_checked": sum(len(c.outputs) for c in code),
            "output_storage": "Checked in memory; no executed notebook artifact required",
            "source_notebook_sha256": source_before}



def verify_transformations(split):
    author = load_definitions(
        NOTEBOOK, {"validate_feature_schema", "FeatureSchemaValidator",
                   "RareCategoryGrouper", "PlaceholderSafeOneHotEncoder",
                   "NativeCategoricalPreprocessor"}, "leng_preprocessing_definitions")
    wanted = set(split.train_ids) | set(split.validation_ids)
    pieces = [chunk.loc[chunk.id.isin(wanted)] for chunk in pd.read_csv(
        SOURCE, usecols=["id"] + FEATURES, dtype={c: "string" for c in CATS},
        chunksize=20000)]
    data = pd.concat(pieces).set_index("id")
    require(data.index.is_unique and set(data.index) == wanted, "Predictor ID coverage mismatch")
    train, valid = data.loc[list(split.train_ids), FEATURES], data.loc[list(split.validation_ids), FEATURES]
    schema = author.FeatureSchemaValidator(FEATURES, CONTS)
    categorical = Pipeline([("rare", author.RareCategoryGrouper(30)),
                            ("encoder", author.PlaceholderSafeOneHotEncoder())])
    glm = Pipeline([("schema", clone(schema)), ("preprocessing", ColumnTransformer(
        [("categorical", categorical, CATS), ("continuous", StandardScaler(), CONTS)],
        sparse_threshold=1.0))])
    native = Pipeline([("schema", clone(schema)),
                       ("preprocessing", author.NativeCategoricalPreprocessor(CATS, 30))])
    glm.fit(train)
    native.fit(train)
    state = pickle.dumps((glm, native))
    sample = valid.sample(180, random_state=391)
    encoded = glm.transform(sample).toarray()
    transformed = native.transform(valid)
    require(encoded.shape == (180, 808) and transformed.shape == (28248, 130),
            "Preprocessing output dimensions mismatch")
    grouper = glm.named_steps["preprocessing"].named_transformers_["categorical"]
    native_fitted = native.named_steps["preprocessing"]
    reference, rare, rare_ids, unseen_ids = [], {}, set(), set()
    unseen_occurrences = 0
    for index, col in enumerate(CATS):
        counts = Counter(train[col])
        rare[col] = {v for v, n in counts.items() if n < 30}
        vocabulary = sorted(v for v, n in counts.items() if n >= 30)
        if rare[col]:
            vocabulary.append("__rare__")
        require(set(grouper.named_steps["rare"].known_levels_[col]) == set(counts)
                and set(grouper.named_steps["rare"].rare_levels_[col]) == rare[col],
                f"GLM training vocabulary/rare mismatch: {col}")
        require(grouper.named_steps["encoder"].encoder_.categories_[index].tolist()
                == sorted(vocabulary), f"GLM one-hot vocabulary mismatch: {col}")
        require(native_fitted.categories_[col] == vocabulary
                and set(native_fitted.rare_levels_[col]) == rare[col]
                and not transformed[col].cat.ordered,
                f"Native training vocabulary mismatch: {col}")
        for level in sorted(vocabulary):
            reference.append([float((v if v in counts and v not in rare[col]
                                     else "__rare__" if rare[col] else "__unseen__") == level)
                              for v in sample[col]])
        mapped = valid[col].map({v: "__rare__" if v in rare[col] else v for v in counts})
        require(transformed[col].astype("string").fillna("<missing>").equals(
            mapped.astype("string").fillna("<missing>")), f"Native validation mapping mismatch: {col}")
        rare_ids.update(valid.index[valid[col].isin(rare[col])])
        unseen = ~valid[col].isin(counts)
        unseen_ids.update(valid.index[unseen])
        unseen_occurrences += int(unseen.sum())
    means = np.array([math.fsum(train[c]) / len(train) for c in CONTS])
    scales = np.array([(math.fsum((v - means[j]) ** 2 for v in train[c]) / len(train)) ** .5
                       for j, c in enumerate(CONTS)])
    expected = np.column_stack([np.array(reference).T, (sample[CONTS].to_numpy() - means) / scales])
    require(np.allclose(encoded, expected, rtol=1e-12, atol=1e-12),
            "GLM values differ from independent one-hot/scaling calculation")
    require(transformed.index.equals(valid.index) and transformed[CONTS].equals(valid[CONTS]),
            "Native IDs/continuous values changed")
    scaler = glm.named_steps["preprocessing"].named_transformers_["continuous"]
    require(scaler.n_samples_seen_ == len(train), "Scaler fitted outside training")
    shuffled = sample.sample(frac=1, random_state=101)
    require(np.array_equal(glm.transform(shuffled).toarray()[
        [shuffled.index.get_loc(i) for i in sample.index]], encoded), "GLM row order mismatch")
    # Independently probe each field's unknown and missing fallback.
    unseen, missing = sample.head(116).copy(), sample.head(116).copy()
    for i, col in enumerate(CATS):
        unseen.iloc[i, unseen.columns.get_loc(col)] = "__leng_unseen__"
        missing.iloc[i, missing.columns.get_loc(col)] = pd.NA
    require(np.array_equal(glm.transform(unseen).toarray(), glm.transform(missing).toarray()),
            "GLM missing/unseen fallbacks differ")
    for probe in (unseen, missing):
        values = native.transform(probe)
        require(all(pd.isna(values.iloc[i][col]) for i, col in enumerate(CATS)),
                "Native unknown/missing fallback mismatch")
    require(pickle.dumps((glm, native)) == state, "Validation changed fitted preprocessing")
    threshold = train.head(59).copy()
    threshold["cat1"] = ["A"] * 29 + ["B"] * 30
    for pipeline in (clone(glm), clone(native)):
        pipeline.fit(threshold)
        prep = pipeline.named_steps["preprocessing"]
        learned = (prep.named_transformers_["categorical"].named_steps["rare"]
                   if isinstance(prep, ColumnTransformer) else prep)
        require(learned.rare_levels_["cat1"] == ["A"], "Rare threshold 29/30 mismatch")
    summary = {
        "training_rare_levels": sum(map(len, rare.values())),
        "fields_with_rare_levels": sum(bool(v) for v in rare.values()),
        "validation_rare_claims": len(rare_ids), "validation_unseen_claims": len(unseen_ids),
        "validation_unseen_occurrences": unseen_occurrences,
        "validation_both": len(rare_ids & unseen_ids), "validation_either": len(rare_ids | unseen_ids),
    }
    require(list(summary.values()) == [352, 30, 490, 12, 13, 3, 499],
            "Independent category impact counts mismatch")
    print("PASS: Independent vocabularies, mappings, scaling, fallbacks, state and ID alignment")
    return {**summary, "glm_output_columns": 808, "native_output_columns": 130,
            "glm_oracle_validation_rows": 180, "predictor_reader_requests_loss": False}


class FixedLogOutputs(RegressorMixin, BaseEstimator):
    def __init__(self, outputs=None):
        self.outputs = outputs

    def fit(self, X, y):
        self.seen_y_ = np.array(y)
        return self

    def predict(self, X):
        return np.array(self.outputs)


def verify_target_inverse():
    author = load_definitions(TARGET_NOTEBOOK, {"LogTargetRegressor"}, "leng_target_definition")
    wrapper = author.LogTargetRegressor
    features, loss = np.zeros((3, 1)), np.array([3., 80., 700.])
    fitted = wrapper(FixedLogOutputs([-40., math.log1p(42.), 800.])).fit(features, loss)
    require(np.allclose(fitted.regressor_.seen_y_, np.log1p(loss)), "Wrong fitted target scale")
    require(np.allclose(fitted.predict(features), [3., 42., 700.]), "Inverse/clipping mismatch")
    for bad in (np.nan, np.inf, -np.inf):
        try:
            wrapper(FixedLogOutputs([bad, 1., 2.])).fit(features, loss).predict(features)
        except ValueError:
            continue
        raise ValueError("Nonfinite target output accepted")
    for bad in ([0., 2., 3.], [-1., 2., 3.], [np.nan, 2., 3.]):
        try:
            wrapper(FixedLogOutputs([1., 2., 3.])).fit(features, bad)
        except ValueError:
            continue
        raise ValueError("Invalid training loss accepted")
    a = wrapper(FixedLogOutputs([1., 2.])).fit(features[:2], loss[:2])
    b = wrapper(FixedLogOutputs([1., 2.])).fit(features[:2], loss[1:])
    require(a.log_upper_ < b.log_upper_ and a.log_lower_ < b.log_lower_,
            "Target bounds not learned from each fit portion")
    print("PASS: Independent synthetic log-target/inverse, per-fit bounds and invalid-value checks")
    return {"fit_transform": "log1p", "inverse": "expm1 after fit-range clipping",
            "invalid_cases_rejected": 6, "uses_real_model_targets": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, help="Write a new technical receipt; never overwrite")
    args = parser.parse_args()
    result = execution_identity()
    _, split = verify_frozen_split()
    result.update(
        notebook=reproduce_notebook(),
        independent_preprocessing=verify_transformations(split),
        target_inverse=verify_target_inverse(),
        test_target_policy="Predictor reader excludes loss; synthetic targets only in model checks",
        status="PASS",
        limitations=["No real candidate CV or performance evaluation",
                     "Notebook self-tests are reproduction evidence; independent oracles are separate",
                     "GLM values checked on 180 validation rows; "
                     "native labels checked on all validation rows"],
    )
    if args.receipt:
        write_receipt(args.receipt, result, [
            Path(__file__).resolve(), ROOT / "scripts/verify_gate2_leng.py", NOTEBOOK,
            TARGET_NOTEBOOK, SOURCE,
            ROOT / "artifacts/october/gate 1/october_partition_manifest.csv",
            ROOT / "environments/gate2/requirements.txt",
        ])



if __name__ == "__main__":
    main()
