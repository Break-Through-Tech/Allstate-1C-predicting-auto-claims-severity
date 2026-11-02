# Gate 2 reproduction environment

Use Python **3.13.5** and the direct dependency pins in [requirements.txt](requirements.txt).
This specification is separate from the historical September dependencies and does
not modify any teammate environment. It is a direct dependency specification, not
a complete cross-platform transitive lock; receipts record the actual interpreter
and versions used. The local verification runs use the existing `allstate-btt`.

From the repository root, create an isolated reproduction environment if needed:

```bash
conda create --name allstate-gate2-repro python=3.13.5 pip
conda activate allstate-gate2-repro
python -m pip install -r environments/gate2/requirements.txt
python -m pip check
```

On **macOS**, install the OpenMP runtime in that new environment as well:

```bash
conda install --name allstate-gate2-repro -c conda-forge llvm-openmp=19.1.7
python -c 'import xgboost; print(xgboost.__version__, xgboost.build_info())'
```

The verified local environment uses this Conda Forge OpenMP version. An existing
Homebrew `libomp` installation can also satisfy some XGBoost builds, but is not
required for the documented Conda route. Do not install both routes merely to
reproduce this run. Linux runtime packaging differs; validate the XGBoost import
on the actual platform rather than assuming a macOS binary is portable.

To use the existing environment without installing or changing anything:

```bash
conda activate allstate-btt
export PYTHONDONTWRITEBYTECODE=1
python -B -m scripts.verify_gate2_leng
python -B -m unittest discover -s tests -p 'test_verify_gate2_leng.py' -v
```

Default test discovery still needs only the existing NumPy/pandas dependencies.
The added tests check that importing the verifier and its evaluator probes works
when scikit-learn, XGBoost and the notebook packages are unavailable. Scikit-learn
is imported only when the full Gate 2 CLI reconstructs CV folds. Notebook tools
are needed only for the separate preprocessing CLI.

Gate 2 preprocessing does not read or validate the Approach 2 configuration.
Use `--approach2-config "artifacts/october/gate 2/approach2_xgboost_config.json"`
on the baseline verifier for the optional static Gate 3 scaffold check.

The verification report at
[leng_gate2_independent_verification.md](../../artifacts/october/gate%202/leng_gate2_independent_verification.md)
contains the exact nine-file proposal, excluded local files and reproduction
commands. The two retained receipts are self-contained summaries; their input
paths refer to retained or already tracked files. Notebook outputs are checked
in memory. Receipt writers refuse to overwrite an existing path, so reproduce
into a new temporary directory. Do not run Rachel's training-fold notebook
as a read-only verifier: it writes teammate-owned configuration/reference files.
