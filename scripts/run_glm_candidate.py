"""Run the frozen Approach 1 search and score its selected candidate once."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import numpy as np
import pandas as pd

from scripts.evaluation import evaluate_mae, load_frozen_split, load_partition_targets, require, sha256
from scripts.verify_gate2_preprocessing_leng import CATS, CONTS, FEATURES, TARGET_NOTEBOOK, load_definitions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-note", required=True)
    args = parser.parse_args()
    gate2 = Path("artifacts/october/gate 2")
    config_path = gate2 / "approach1_glm_config.json"
    config = json.loads(config_path.read_text())
    fold_path = Path(config["inputs"]["cv_folds"])
    metadata = json.loads(fold_path.with_name("october_cv_folds_metadata.json").read_text())
    run_id = f"glm-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    out = Path("artifacts/october/gate 3/runs") / run_id
    out.mkdir(parents=True)
    print(out, flush=True)
    receipt = {
        "run_id": run_id, "approval_note": args.approval_note, "config": config,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "environment": {p: version(p) for p in ("numpy", "pandas", "scipy", "scikit-learn")},
        "status": "failed", "test_used": False, "validation_score_attempted": False,
    }
    started = perf_counter()
    rows = []
    try:
        split = load_frozen_split()
        receipt["input_sha256"] = {str(p): sha256(p) for p in (
            config_path, fold_path, TARGET_NOTEBOOK, Path(__file__),
            Path("scripts/evaluation.py"), Path("scripts/verify_gate2_preprocessing_leng.py"))}
        receipt.update(source_sha256=split.source_sha256, manifest_sha256=split.manifest_sha256,
                       manifest_id=split.manifest_id, training_claims=len(split.train_ids))
        require(split.manifest_id == config["inputs"]["split_manifest"]
                and split.manifest_sha256 == metadata["manifest_sha256"]
                and sha256(fold_path) == metadata["fold_file_sha256"], "Split or fold mismatch")
        folds = pd.read_csv(fold_path).set_index("id").sort_index()
        require(folds.index.is_unique and set(folds.index) == set(split.train_ids)
                and set(folds.fold) == set(range(5)), "Unexpected fold membership")
        definitions = load_definitions(TARGET_NOTEBOOK, {
            "validate_feature_schema", "FeatureSchemaValidator", "RareCategoryGrouper",
            "PlaceholderSafeOneHotEncoder", "LogTargetRegressor", "build_glm_preprocessing",
            "build_glm_pipeline",
        }, "candidate_definitions", {
            "config": config, "FEATURE_COLUMNS": FEATURES, "CATEGORICAL_COLUMNS": CATS,
            "CONTINUOUS_COLUMNS": CONTS, "RARE_THRESHOLD": config["preprocessing"]["rare_min_count"],
        })
        train, validation = load_partition_targets(split)
        wanted = set(split.train_ids) | set(split.validation_ids)
        inputs = pd.concat(chunk.loc[chunk.id.isin(wanted)] for chunk in pd.read_csv(
            split.source_path, usecols=["id", *FEATURES], dtype={c: "string" for c in CATS},
            chunksize=20_000)).set_index("id")
        require(inputs.index.is_unique and set(inputs.index) == wanted, "Input coverage mismatch")
        y = train.set_index("id").loss
        alphas = config["search_space"]["alpha"]
        for fold in range(5):
            fit_ids = folds.index[folds.fold != fold]
            held_ids = folds.index[folds.fold == fold]
            prep = definitions.build_glm_pipeline(alphas[0]).named_steps["preprocessing"]
            fit_inputs = prep.fit_transform(inputs.loc[fit_ids, FEATURES])
            held_inputs = prep.transform(inputs.loc[held_ids, FEATURES])
            for alpha in alphas:
                fit_start = perf_counter()
                model = definitions.build_glm_pipeline(alpha).named_steps["model"]
                model.fit(fit_inputs, y.loc[fit_ids])
                errors = np.abs(model.predict(held_inputs) - y.loc[held_ids].to_numpy())
                rows.append(dict(alpha=alpha, fold=fold, claims=len(held_ids),
                                 mae=float(errors.mean()), absolute_error_sum=float(errors.sum()),
                                 model_seconds=perf_counter() - fit_start))
            print(f"Fold {fold + 1}/5 complete", flush=True)
        cv = pd.DataFrame(rows)
        pooled = cv.groupby("alpha").absolute_error_sum.sum() / len(train)
        selected = float(max(pooled.index[pooled <= pooled.min() + 1]))
        receipt.update(selected_alpha=selected, pooled_cv_mae=pooled.to_dict(),
                       fold_mae_summary=cv.groupby("alpha").mae.agg(["mean", "std"]).to_dict("index"))
        model = definitions.build_glm_pipeline(selected)
        model.fit(inputs.loc[y.index, FEATURES], y)
        ids = validation.id
        predictions = pd.DataFrame({"id": ids, "prediction": model.predict(inputs.loc[ids, FEATURES])})
        prediction_path = out / "validation_predictions.csv"
        predictions.to_csv(prediction_path, index=False)
        receipt["prediction_sha256"] = sha256(prediction_path)
        receipt["validation_score_attempted"] = True
        receipt["validation"] = evaluate_mae(validation, predictions, split=split,
                                            run_metadata={"run_id": run_id, "alpha": selected})
        receipt["status"] = "completed"
        print(json.dumps(receipt["validation"], indent=2))
    except BaseException as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        receipt["runtime_seconds"] = perf_counter() - started
        pd.DataFrame(rows).to_csv(out / "cv_results.csv", index=False)
        (out / "run_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
