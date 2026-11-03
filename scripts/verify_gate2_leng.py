"""Leng's independent Gate 2 source, baseline, prediction and CV verification.

Run: python -m scripts.verify_gate2_leng
No model is trained. Test rows are skipped before converting loss. Preprocessing
is checked separately by scripts.verify_gate2_preprocessing_leng. Only an explicit
--receipt writes a new file; existing evidence is never overwritten.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import re
import shlex
import statistics
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

# The shared evaluator is the subject of comparison, never the numerical oracle.
from scripts.evaluation import EvaluationError, FrozenSplit, evaluate_mae

GATE1 = ROOT / "artifacts/october/gate 1"
GATE2 = ROOT / "artifacts/october/gate 2"
SOURCE = ROOT / "data/allstate_claims_data.csv"
MANIFEST = GATE1 / "october_partition_manifest.csv"
METADATA = GATE1 / "october_split_metadata.json"
FOLD_FILE = GATE2 / "cv_folds/october_cv_folds.csv"
FOLD_METADATA = FOLD_FILE.with_name("october_cv_folds_metadata.json")
SOURCE_SHA = "74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03"
MANIFEST_SHA = "18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1"
EXPECTED_COUNTS = {"train": 141238, "validation": 28248, "test": 18832}
EXPECTED_MAE = {"mean": 1959.630916, "median": 1802.793854}


class VerificationError(ValueError):
    """A required check failed; also active under python -O."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def close(actual, expected, label, *, abs_tol=1e-9):
    require(math.isclose(float(actual), float(expected), rel_tol=1e-12,
                         abs_tol=abs_tol), f"{label}: {actual!r} != {expected!r}")


def sha256_file(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"{path}: duplicate JSON key {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_keys)


def canonical_id(value):
    require(isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value),
            f"Noncanonical CSV claim ID: {value!r}")
    number = int(value)
    require(number <= np.iinfo(np.int64).max, "Claim ID exceeds int64")
    return number


def verify_frozen_split():
    metadata = load_json(METADATA)
    acceptance_path = GATE1 / "split_acceptance.json"
    acceptance = load_json(acceptance_path)
    require(sha256_file(SOURCE) == metadata["source"]["sha256"] == SOURCE_SHA,
            "Frozen source SHA-256 mismatch")
    require(SOURCE.stat().st_size == metadata["source"]["bytes"], "Source size mismatch")
    require(sha256_file(MANIFEST) == metadata["artifacts_sha256"][MANIFEST.name]
            == MANIFEST_SHA, "Frozen partition SHA-256 mismatch")
    require(acceptance["status"] == "accepted_for_baselines"
            and acceptance["source_sha256"] == SOURCE_SHA
            and acceptance["manifest_sha256"] == MANIFEST_SHA
            and acceptance["manifest_id"] == metadata["split"]["version"] == "october-split-v1"
            and acceptance["partition_counts"] == EXPECTED_COUNTS,
            "Baseline split acceptance identity mismatch")
    manifest = pd.read_csv(MANIFEST, dtype={"id": "string"}, keep_default_na=False)
    require(manifest.columns.tolist() == ["id", "partition"], "Manifest schema mismatch")
    manifest["id"] = [canonical_id(i) for i in manifest.id]
    require(manifest.id.is_unique and not manifest.isna().any().any(),
            "Duplicate/missing manifest IDs")
    require(manifest.partition.value_counts().to_dict() == EXPECTED_COUNTS,
            "Partition counts mismatch")
    require(acceptance["seed"] == metadata["split"]["seed"] == 42
            and acceptance["proportions_percent"] == metadata["split"]["proportions_percent"]
            == {"train": 75, "validation": 15, "test": 10}, "Frozen split settings mismatch")
    ranked = sorted(manifest.id, key=lambda i: (
        hashlib.sha256(f"october-split-v1|42|{i}".encode("ascii")).digest(), i))
    rebuilt = {}
    offset = 0
    for name, count in EXPECTED_COUNTS.items():
        rebuilt.update(dict.fromkeys(ranked[offset:offset + count], name))
        offset += count
    require(rebuilt == dict(zip(manifest.id, manifest.partition)),
            "Independent ID-only partition reconstruction mismatch")
    split = FrozenSplit(
        SOURCE, SOURCE_SHA, MANIFEST, MANIFEST_SHA, "october-split-v1",
        *(tuple(sorted(manifest.loc[manifest.partition.eq(p), "id"]))
          for p in ("train", "validation", "test")),
        sha256_file(METADATA), sha256_file(acceptance_path),
    )
    split.validate()
    print("PASS: Frozen source, split acceptance, schema, IDs, counts and ID-only assignment")
    return manifest, split


def read_development_targets(path, train_ids, valid_ids, test_ids):
    """Independent reader: skip test rows BEFORE loss conversion."""
    groups = [set(train_ids), set(valid_ids), set(test_ids)]
    require(sum(map(len, groups)) == len(set.union(*groups)), "Partitions overlap")
    training, validation, seen = {}, {}, set()
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            claim = canonical_id(row["id"])
            require(claim not in seen, "Duplicate source claim ID")
            seen.add(claim)
            if claim in groups[2]:
                continue
            require(claim in groups[0] or claim in groups[1], "Unexpected source ID")
            loss = float(row["loss"])
            require(math.isfinite(loss) and loss > 0, "Invalid development loss")
            (training if claim in groups[0] else validation)[claim] = loss
    require(seen == set.union(*groups), "Source/manifest population mismatch")
    require(set(training) == groups[0] and set(validation) == groups[1],
            "Development target coverage mismatch")
    return training, validation


def verify_baselines(split):
    training, validation = read_development_targets(
        SOURCE, split.train_ids, split.validation_ids, split.test_ids)
    constants = {"mean": math.fsum(training.values()) / len(training),
                 "median": statistics.median(training.values())}
    scores = {}
    for name, constant in constants.items():
        scores[name] = math.fsum(abs(y - constant) for y in validation.values()) / len(validation)
        close(scores[name], EXPECTED_MAE[name], f"Reference {name} MAE", abs_tol=1e-6)
        print(f"PASS: Independent {name}: constant={constant:.12f}, MAE={scores[name]:.12f}")
    return training, validation, constants, scores


def read_prediction_csv(path, expected_ids):
    """Check saved CSV coverage before involving the shared evaluator."""
    predictions = {}
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == ["id", "prediction"], "Prediction CSV schema mismatch")
        for row in reader:
            require(None not in row and row["prediction"] is not None, "Malformed prediction row")
            claim = canonical_id(row["id"])
            require(claim not in predictions, "Duplicate prediction ID")
            value = float(row["prediction"])
            require(math.isfinite(value), "Nonfinite saved prediction")
            predictions[claim] = value
    expected = set(expected_ids)
    require(bool(expected) and set(predictions) == expected,
            f"Prediction coverage: {len(expected - set(predictions))} missing, "
            f"{len(set(predictions) - expected)} extra")
    return predictions


def independent_mae(truth, predictions):
    require(bool(truth) and set(truth) == set(predictions), "MAE ID coverage mismatch")
    result = math.fsum(abs(truth[i] - predictions[i]) for i in sorted(truth)) / len(truth)
    require(math.isfinite(result), "Independent MAE is nonfinite")
    return result


def verify_prediction_run(directory, split, validation, constants):
    directory = Path(directory)
    receipt_path = directory / "baseline_run_receipt.json"
    receipt = load_json(receipt_path)
    require(receipt["run_id"] == directory.name, "Baseline run/directory identity mismatch")
    identities = {
        "source_sha256": split.source_sha256, "manifest_sha256": split.manifest_sha256,
        "manifest_id": split.manifest_id, "metadata_sha256": split.metadata_sha256,
        "acceptance_sha256": split.acceptance_sha256, "train_claim_count": len(split.train_ids),
        "validation_claim_count": len(validation),
    }
    for key, expected in identities.items():
        require(receipt[key] == expected, f"Baseline receipt {key} mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", receipt["code_version"]), "Missing code commit identity")
    commit = subprocess.run(
        ["git", "cat-file", "-e", receipt["code_version"] + "^{commit}"],
        cwd=ROOT, capture_output=True,
    )
    # A shallow checkout may lack old commit objects. Artifact/hash checks below
    # remain mandatory; record historical availability as a provenance limitation.
    recorded_commit_available = commit.returncode == 0
    require(receipt["automated_tests"]["exit_code"] == 0
            and bool(receipt["checks"]) and all(receipt["checks"].values()),
            "Recorded baseline checks did not pass")
    require(len(receipt["results"]) == 2
            and {r["baseline_name"] for r in receipt["results"]} == {"mean", "median"},
            "Receipt must contain exactly both baselines")
    comparison = directory / "baseline_comparison.csv"
    require(sha256_file(comparison) == receipt["comparison_sha256"], "Comparison artifact hash mismatch")
    table = pd.read_csv(comparison, float_precision="round_trip")
    require(len(table) == 2 and set(table.baseline_name) == {"mean", "median"},
            "Comparison table baseline coverage mismatch")
    truth_frame = pd.DataFrame(list(validation.items()), columns=["id", "loss"])
    verified = []
    for result in receipt["results"]:
        name = result["baseline_name"]
        path = directory / f"baseline_{name}_predictions.csv"
        require(Path(result["prediction_artifact"]).name == path.name,
                "Receipt prediction filename mismatch")
        require(sha256_file(path) == result["prediction_sha256"], "Prediction artifact hash mismatch")
        predictions = read_prediction_csv(path, validation)
        close(result["fitted_constant"], constants[name], f"{name} fitted constant")
        require(all(p == result["fitted_constant"] for p in predictions.values()),
                "Exported predictions differ from the recorded fitted constant")
        score = independent_mae(validation, predictions)
        predicted = pd.DataFrame(list(predictions.items()), columns=["id", "prediction"])
        shared = evaluate_mae(truth_frame.iloc[::-1], predicted.sample(frac=1, random_state=91),
                              split=split)
        for actual in (shared, result):
            close(actual["mae"], score, f"{name} shared/recorded MAE")
            require(actual["evaluated_claim_count"] == len(validation)
                    and actual["manifest_sha256"] == split.manifest_sha256
                    and actual["source_sha256"] == split.source_sha256
                    and actual["partition"] == "validation"
                    and actual["metric"] == "MAE" and actual["units"] == "original loss units",
                    "Evaluation identity/count/units mismatch")
        require(result["run_metadata"]["run_id"] == receipt["run_id"]
                and result["run_metadata"]["baseline"] == name
                and all(result["checks"].values()), "Baseline result metadata/check mismatch")
        row = table.loc[table.baseline_name.eq(name)].iloc[0]
        close(row.validation_mae, score, "Comparison MAE")
        close(row.fitted_constant, constants[name], "Comparison fitted constant")
        require(row.run_id == receipt["run_id"] and row.code_version == receipt["code_version"]
                and row.manifest_id == split.manifest_id and row.source_version == split.source_sha256
                and row.train_claim_count == len(split.train_ids)
                and row.validation_claim_count == len(validation), "Comparison identity mismatch")
        verified.append({"baseline": name, "mae": score, "claims": len(predictions),
                         "prediction_sha256": sha256_file(path)})
    code_identity = {}
    for path in ("scripts/evaluation.py", "scripts/run_baselines.py"):
        recorded = receipt["code_sha256"][path]
        require(re.fullmatch(r"[0-9a-f]{64}", recorded), "Invalid baseline code hash")
        code_identity[path] = {
            "recorded_sha256": recorded, "current_sha256": sha256_file(ROOT / path),
            "matches_current": recorded == sha256_file(ROOT / path),
        }
    print(f"PASS: {directory.name}: prediction IDs, values, hashes, MAE and evaluator agreement")
    return {"run_id": receipt["run_id"], "receipt_sha256": sha256_file(receipt_path),
            "recorded_commit_available": recorded_commit_available,
            "receipt_path": str(receipt_path.relative_to(ROOT))
            if receipt_path.is_relative_to(ROOT) else str(receipt_path),
            "comparison_sha256": sha256_file(comparison),
            "recorded_code_version": receipt["code_version"],
            "recorded_environment": {k: receipt[k] for k in ("python", "numpy", "pandas")},
            "code_identity": code_identity, "results": verified}


def verify_synthetic_evaluator():
    split = FrozenSplit(Path("unused"), "a" * 64, Path("unused"), "b" * 64,
                        "leng-synthetic", (1, 2), (3, 4, 5), (6,), "c" * 64, "d" * 64)
    truth = pd.DataFrame({"id": [5, 3, 4], "loss": [17., 2., 100.]})
    predictions = pd.DataFrame({"id": [4, 5, 3], "prediction": [90., 19., -3.]})
    expected = independent_mae({5: 17., 3: 2., 4: 100.}, {4: 90., 5: 19., 3: -3.})
    close(expected, 17 / 3, "Hand-calculated nonconstant MAE")
    for y, p in ((truth, predictions), (truth.iloc[::-1], predictions.iloc[::-1])):
        close(evaluate_mae(y, p, split=split)["mae"], expected, "Nonconstant shuffled MAE")
    bad_predictions = {
        "missing": predictions.iloc[:2], "empty": predictions.iloc[:0],
        "duplicate": pd.concat([predictions, predictions.iloc[:1]]),
        "extra": pd.concat([predictions, pd.DataFrame({"id": [7], "prediction": [1.]})]),
        "test ID": predictions.assign(id=[4, 5, 6]),
        "wrong schema": predictions.rename(columns={"prediction": "wrong"}),
        "numeric strings": predictions.assign(prediction=["90", "19", "-3"]),
        "boolean predictions": predictions.assign(prediction=True),
        "complex predictions": predictions.assign(prediction=1 + 2j),
    }
    for value in (np.nan, np.inf, -np.inf):
        bad_predictions[f"nonfinite {value}"] = predictions.assign(prediction=[90., value, -3.])
    for value in (None, True, 0, -1, 4.0, "04", "bad"):
        frame = predictions.astype({"id": object})
        frame.loc[0, "id"] = value
        bad_predictions[f"invalid ID {value!r}"] = frame
    bad_truth = {"duplicate truth": pd.concat([truth, truth.iloc[:1]]),
                 "missing truth": truth.iloc[:2], "extra truth column": truth.assign(extra=1)}
    for value in (0., -1., np.nan, np.inf):
        bad_truth[f"invalid loss {value}"] = truth.assign(loss=[value, 2., 100.])
    for label, frame in bad_predictions.items():
        try:
            evaluate_mae(truth, frame, split=split)
        except EvaluationError:
            continue
        raise VerificationError(f"Shared evaluator accepted {label}")
    for label, frame in bad_truth.items():
        try:
            evaluate_mae(frame, predictions, split=split)
        except EvaluationError:
            continue
        raise VerificationError(f"Shared evaluator accepted {label}")
    count = len(bad_predictions) + len(bad_truth)
    print(f"PASS: Nonconstant aligned MAE, unchanged negative prediction and {count} invalid cases")
    return {"nonconstant_mae": expected, "invalid_cases_rejected": count,
            "cases": list(bad_predictions) + list(bad_truth)}


def verify_cv_folds(manifest, training):
    # Modeling dependencies are needed by this CLI check, not by test discovery.
    from sklearn.model_selection import KFold

    saved = pd.read_csv(FOLD_FILE)
    metadata = load_json(FOLD_METADATA)
    ids = np.sort(manifest.loc[manifest.partition.eq("train"), "id"].to_numpy())
    numbers = np.full(len(ids), -1, dtype=np.int64)
    for k, (_, held_out) in enumerate(KFold(5, shuffle=True, random_state=42).split(ids)):
        numbers[held_out] = k
    require(saved.equals(pd.DataFrame({"id": ids, "fold": numbers})),
            "Saved folds differ from sorted-ID KFold reconstruction")
    # Second reconstruction uses the documented permutation, without calling KFold.
    independent = np.empty(len(ids), dtype=np.int64)
    for k, portion in enumerate(np.array_split(np.random.RandomState(42).permutation(len(ids)), 5)):
        independent[portion] = k
    require(np.array_equal(numbers, independent), "Independent fold permutation mismatch")
    counts = saved.fold.value_counts().sort_index().to_dict()
    require(saved.id.is_unique and set(saved.id) == set(ids)
            and counts == dict(enumerate([28248, 28248, 28248, 28247, 28247])),
            "CV membership/count mismatch")
    require(sha256_file(FOLD_FILE) == metadata["fold_file_sha256"]
            and metadata["manifest_sha256"] == MANIFEST_SHA
            and metadata["source_sha256"] == SOURCE_SHA
            and metadata["training_claims"] == len(ids)
            and metadata["held_out_counts"] == {str(k): v for k, v in counts.items()},
            "CV metadata identity mismatch")
    reference = pd.read_csv(FOLD_FILE.with_name("cv_constant_baselines.csv"))
    require(len(reference) == 15 and not reference.duplicated(["fold", "constant"]).any(),
            "CV constant reference coverage mismatch")
    pooled = {}
    for k in range(5):
        fit = [training[i] for i in saved.loc[saved.fold.ne(k), "id"]]
        held = [training[i] for i in saved.loc[saved.fold.eq(k), "id"]]
        constants = {"mean": math.fsum(fit) / len(fit), "median": statistics.median(fit),
                     "expm1(mean of log1p)": math.expm1(math.fsum(map(math.log1p, fit)) / len(fit))}
        for name, constant in constants.items():
            rows = reference.loc[reference.fold.eq(k) & reference.constant.eq(name)]
            require(len(rows) == 1 and rows.iloc[0].claims == len(held), "CV constant row mismatch")
            score = math.fsum(abs(y - constant) for y in held) / len(held)
            # Teammate CSV deliberately retains only ten significant figures.
            close(rows.iloc[0].value, constant, "CV constant", abs_tol=5e-6)
            close(rows.iloc[0].MAE, score, "CV MAE", abs_tol=5e-6)
            pooled[name] = pooled.get(name, 0.) + score * len(held) / len(ids)
    print("PASS: Both CV reconstructions, five training-only folds, hashes and 15 CV constants")
    return {"held_out_counts": counts, "fold_sha256": sha256_file(FOLD_FILE),
            "cv_constant_pooled_mae": pooled}


def verify_proposed_config(path):
    """Optional static Gate 3 scaffold review; never fit or select a model."""
    config = load_json(path)
    require(config["execution"]["training_authorized"] is False,
            "Proposed scaffold must retain its training hold")
    policy = config["policy_review"]
    require(policy["status"] == "PENDING_TEAM_DECISION"
            and policy["selected_option"] is None and policy["decision_record"] is None
            and {option["id"] for option in policy["options"]}
            == {"gate1_two_releases", "amend_to_one_release"},
            "Release-sequence decision must remain explicitly unresolved")
    budget = config["experiment_budget"]
    candidates = config["initial_candidates"]
    require(len(candidates) == len({c["id"] for c in candidates}) == 5
            and budget["initial_configurations"] == 5
            and budget["reserved_iteration_configurations"] == 1
            and budget["max_configurations"] == 6
            and budget["cv_folds_per_configuration"] == 5
            and budget["maximum_cv_fits"] == 30
            and budget["early_stopping"] is False, "Approach 2 budget mismatch")
    require(config["inputs"]["source_sha256"] == SOURCE_SHA
            and config["inputs"]["manifest_sha256"] == MANIFEST_SHA
            and config["inputs"]["cv_folds_sha256"] == sha256_file(FOLD_FILE),
            "Approach 2 input identity mismatch")
    model = config["model"]
    require(config["environment"]["xgboost"] == "3.1.1"
            and model["objective"] == "reg:absoluteerror" and model["eval_metric"] == "mae"
            and model["tree_method"] == "hist" and model["enable_categorical"] is True,
            "Approach 2 objective/categorical settings mismatch")
    print("PASS: Optional proposed config: static safeguards, identities and 6 x 5 budget")
    return {"config_sha256": sha256_file(path), "training_authorized": False,
            "policy_decision": policy["status"], "selected_option": None,
            "decision_record": None, "initial_configurations": 5,
            "reserved_iteration_configurations": 1, "maximum_cv_fits": 30,
            "scope": "Static review only; no model fit, tuning, release or team approval"}


def execution_identity():
    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        ).strip()
    now = datetime.now(timezone.utc)
    return {"run_id": now.strftime("leng-gate2-%Y%m%dT%H%M%S.%fZ"),
            "timestamp_utc": now.isoformat(),
            "base_commit": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
            "working_tree": git("status", "--porcelain"), "python": platform.python_version(),
            "tracked_diff": git("diff", "--name-only"),
            "staged_diff": git("diff", "--cached", "--name-only"),
            "python_optimized": bool(sys.flags.optimize), "interpreter": sys.executable,
            "environment": {p: version(p) for p in (
                "numpy", "pandas", "scipy", "scikit-learn", "xgboost", "nbformat",
                "nbclient", "ipykernel", "jupyter_client")},
            "execution_command": shlex.join([sys.executable, *sys.orig_argv[1:]]),
            "gate_approval": "NOT RECORDED; technical verification only"}


def write_receipt(path, result, inputs):
    result["input_sha256"] = {str(p.relative_to(ROOT)): sha256_file(p) for p in inputs}
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x") as handle:
        handle.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Receipt: {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-run", action="append", type=Path, default=[],
                        help="Also verify this reproduced baseline directory")
    parser.add_argument("--receipt", type=Path, help="Write a new technical receipt; never overwrite")
    parser.add_argument("--approach2-config", type=Path,
                        help="Optional static review of the proposed Gate 3 config")
    args = parser.parse_args()
    result = execution_identity()
    manifest, split = verify_frozen_split()
    training, validation, constants, scores = verify_baselines(split)
    recorded = sorted((GATE2 / "baselines").glob("*/baseline_run_receipt.json"))
    require(bool(recorded), "No recorded baseline receipts found")
    runs = [p.parent for p in recorded]
    result.update(
        constants=constants, validation_mae=scores, partition_counts=EXPECTED_COUNTS,
        source_sha256=SOURCE_SHA, manifest_sha256=MANIFEST_SHA,
        baseline_runs=[verify_prediction_run(p, split, validation, constants) for p in runs],
        synthetic_evaluator=verify_synthetic_evaluator(), cv=verify_cv_folds(manifest, training),
        test_target_policy="Test rows skipped before loss conversion; no test targets scored",
        status="PASS",
    )
    if args.baseline_run:
        reproduced = []
        committed_hashes = {r["prediction_sha256"] for run in result["baseline_runs"]
                            for r in run["results"]}
        for directory in args.baseline_run:
            run = verify_prediction_run(directory, split, validation, constants)
            require(all(r["prediction_sha256"] in committed_hashes for r in run["results"])
                    and all(r["matches_current"] for r in run["code_identity"].values()),
                    "Fresh reproduction differs from committed predictions/current code")
            run.pop("receipt_path")
            reproduced.append(run)
        result["baseline_reproduction"] = {
            "runs": reproduced,
            "artifact_policy": "Fresh temporary outputs are not required by the submission; "
                               "their prediction bytes match the committed baseline artifacts.",
        }
    if args.approach2_config:
        result["approach2_scaffold"] = verify_proposed_config(args.approach2_config)
    if args.receipt:
        inputs = [
            Path(__file__).resolve(), SOURCE, MANIFEST, METADATA, GATE1 / "split_acceptance.json",
            FOLD_FILE, FOLD_METADATA, FOLD_FILE.with_name("cv_constant_baselines.csv"),
            ROOT / "scripts/evaluation.py", ROOT / "scripts/run_baselines.py",
            ROOT / "tests/test_verify_gate2_leng.py", ROOT / "environments/gate2/requirements.txt",
        ]
        if args.approach2_config:
            inputs.append(args.approach2_config.resolve())
        write_receipt(args.receipt, result, inputs)
    print("ALL INDEPENDENT SCRIPT CHECKS PASSED (not a Gate approval)")


if __name__ == "__main__":
    main()
