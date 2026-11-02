"""Failure-path tests for Leng's verifier; no real targets or repository writes."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_gate2_leng as verify


class IndependentVerificationTests(unittest.TestCase):
    def test_default_import_without_gate2_modeling_packages(self):
        code = """
import importlib.abc
import sys
class BlockModelingImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {
            'sklearn', 'xgboost', 'nbformat', 'nbclient', 'ipykernel', 'jupyter_client'
        }:
            raise ModuleNotFoundError('Simulated base environment', name=fullname)
sys.meta_path.insert(0, BlockModelingImports())
from scripts.verify_gate2_leng import verify_synthetic_evaluator
verify_synthetic_evaluator()
"""
        result = subprocess.run([sys.executable, "-B", "-c", code],
                                cwd=verify.ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_optional_config_remains_unapproved(self):
        source = verify.GATE2 / "approach2_xgboost_config.json"
        # Task 8 test discovery remains usable without the optional Gate 3 file.
        if not source.exists():
            self.skipTest("Approach 2 scaffold is not present")
        result = verify.verify_proposed_config(source)
        self.assertFalse(result["training_authorized"])
        original = json.loads(source.read_text())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            for change in ("authorize", "choose_policy", "exceed_budget"):
                config = json.loads(json.dumps(original))
                if change == "authorize":
                    config["execution"]["training_authorized"] = True
                elif change == "choose_policy":
                    config["policy_review"]["selected_option"] = "gate1_two_releases"
                else:
                    config["experiment_budget"]["maximum_cv_fits"] = 35
                path.write_text(json.dumps(config))
                with self.subTest(change=change), self.assertRaises(verify.VerificationError):
                    verify.verify_proposed_config(path)

    def test_prediction_csv_rejections(self):
        cases = {
            "duplicate": "id,prediction\n3,10\n3,20\n",
            "missing": "id,prediction\n3,10\n",
            "extra": "id,prediction\n3,10\n4,20\n5,30\n",
            "replaced": "id,prediction\n3,10\n5,20\n",
            "nonfinite": "id,prediction\n3,nan\n4,20\n",
            "fractional ID": "id,prediction\n3.0,10\n4,20\n",
            "noncanonical ID": "id,prediction\n03,10\n4,20\n",
            "schema": "id,wrong\n3,10\n4,20\n",
            "malformed": "id,prediction\n3,10,extra\n4,20\n",
            "empty": "id,prediction\n",
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.csv"
            for label, contents in cases.items():
                path.write_text(contents)
                with self.subTest(label=label), self.assertRaises(ValueError):
                    verify.read_prediction_csv(path, {3, 4})

    def test_saved_nonconstant_alignment_and_negative_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.csv"
            path.write_text("id,prediction\n4,90\n5,19\n3,-3\n")
            predicted = verify.read_prediction_csv(path, {3, 4, 5})
            self.assertAlmostEqual(verify.independent_mae({5: 17., 3: 2., 4: 100.}, predicted), 17 / 3)

    def test_duplicate_source_rows_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            path.write_text("id,loss\n1,10\n1,20\n2,30\n3,40\n")
            with self.assertRaisesRegex(verify.VerificationError, "Duplicate source"):
                verify.read_development_targets(path, {1}, {2}, {3})

    def test_poisoned_test_target_is_never_converted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            path.write_text("id,loss\n1,10\n2,20\n3,DO_NOT_PARSE_TEST_LOSS\n")
            self.assertEqual(verify.read_development_targets(path, {1}, {2}, {3}),
                             ({1: 10.}, {2: 20.}))

    def test_source_coverage_and_loss_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            for contents in ("id,loss\n1,10\n3,sealed\n",
                             "id,loss\n1,-1\n2,20\n3,sealed\n"):
                path.write_text(contents)
                with self.assertRaises(ValueError):
                    verify.read_development_targets(path, {1}, {2}, {3})

    def test_wrong_score_rejected_including_optimized_python(self):
        with self.assertRaises(verify.VerificationError):
            verify.close(18., 1959.630916, "deliberately wrong baseline")
        result = subprocess.run(
            [sys.executable, "-B", "-O", "-c",
             "from scripts.verify_gate2_leng import close; "
             "close(18., 1959.630916, 'deliberately wrong baseline')"],
            cwd=verify.ROOT, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VerificationError", result.stderr)

    def test_no_removable_assertions_in_independent_verifiers(self):
        for path in (Path(verify.__file__), verify.ROOT / "scripts/verify_gate2_preprocessing_leng.py"):
            nodes = ast.walk(ast.parse(path.read_text()))
            self.assertFalse(any(isinstance(node, ast.Assert) for node in nodes), str(path))

    def test_shared_evaluator_independent_contract_probes(self):
        result = verify.verify_synthetic_evaluator()
        self.assertEqual(result["invalid_cases_rejected"], 26)

    def test_json_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            path.write_text('{"key": 1, "key": 2}')
            with self.assertRaisesRegex(verify.VerificationError, "duplicate JSON key"):
                verify.load_json(path)

    def test_receipt_writes_cannot_overwrite_existing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipt.json"
            path.write_text("original")
            with self.assertRaises(FileExistsError):
                verify.write_receipt(path, {"status": "PASS"}, [])
            self.assertEqual(path.read_text(), "original")

    def test_corrupted_prediction_artifact_fails_before_scoring(self):
        # Copy only to a temporary directory. Never alter the committed baseline.
        import shutil

        source = sorted((verify.GATE2 / "baselines").glob("*/baseline_run_receipt.json"))[-1].parent
        _, split = verify.verify_frozen_split()
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / source.name
            shutil.copytree(source, destination)
            with (destination / "baseline_mean_predictions.csv").open("a") as handle:
                handle.write("999999,0\n")
            # No actual losses needed: receipt/count checks use only frozen IDs.
            validation = dict.fromkeys(split.validation_ids, 1.)
            # Artifact checks must still run in a shallow checkout without old commits.
            missing_commit = subprocess.CompletedProcess([], 1)
            with patch.object(verify.subprocess, "run", return_value=missing_commit), \
                    self.assertRaisesRegex(verify.VerificationError, "artifact hash mismatch"):
                verify.verify_prediction_run(destination, split, validation, {"mean": 1., "median": 1.})


if __name__ == "__main__":
    unittest.main()
