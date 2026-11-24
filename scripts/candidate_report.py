"""Verify saved October evidence and generate a provisional decision; no fitting."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import uuid
import numpy as np
import pandas as pd
from scripts.evaluation import ROOT, require, sha256, load_frozen_split, load_partition_targets, evaluate_mae
from scripts.model_comparison import (BASELINE, read_predictions, score_existing, candidate_decision,
                                      diagnostic_summaries, stability)

G3 = Path('artifacts/october/gate 3')
GLM = G3 / 'comparison_inputs/glm-20261103T055706Z-0748a4b5'
XGB = G3 / 'runs/xgboost-task4'
OLD = G3 / 'comparisons/comparison-20261107T175139Z-d1372e77'
POLICY = G3 / 'xgboost_readiness_decision_20261112.md'
EVIDENCE = [Path('Challenge-Project-Overview.md'), Path('notebooks/data-understanding.ipynb'),
            *[Path('artifacts/september')/x for x in ['artifact_manifest.json','source_profile.csv','target_summary.csv',
              'categorical_inventory.csv','continuous_inventory.csv','findings_register.md','september_report.md',
              'october_recommendation_register.csv','october_modeling_handoff.md','data_dictionary_v1.1.0.csv']],
            Path('artifacts/october/gate 1/gate1_signoff.md'),Path('artifacts/october/gate 1/gate1_overview.md'),
            Path('docs/october_split_design.md'),POLICY,G3/'approach1_glm_record.md',G3/'approach2_xgboost_record.md',
            Path('scripts/run_baselines.py'),Path('scripts/run_xgboost.py'),Path('notebooks/gate2_preprocessing.ipynb'),
            Path('notebooks/gate2_training_folds.ipynb'),Path('notebooks/gate3_approach1_glm.ipynb')]

NEXT = {
 'observed_problem':'Historical EDA exposure, anonymous predictor timing, no independent prospective evidence; large-loss underprediction.',
 'hypothesis':'The frozen A2-C03 configuration retains improvement over both frozen constants on genuinely independent claims with verified filing-time inputs.',
 'change':'Evaluate the unchanged retained model on newly supplied, temporally separated claims after agreeing a protocol; do not tune on that cohort.',
 'controls':'Freeze depth 7, 300 trees, seed 42, preprocessing, existing baseline constants, original-unit MAE and training-derived diagnostic thresholds; preserve existing partitions.',
 'metric':'Original-scale MAE on identical new cohort IDs; high-loss diagnostics reported separately.',
 'success_criterion':'Strictly lower MAE than both frozen constants; exact claim coverage and valid filing-time provenance. Pre-register uncertainty and business criteria before results are seen.',
 'dependencies':'Advisor/team-approved protocol, feature definitions and lineage, prediction/outcome timestamps, independent data access, governance review and execution resources.',
 'risks':'Temporal/group dependence, distribution shift, limited high-loss support and business relevance remain unresolved. Further validation-driven tuning requires a revised team-approved evaluation strategy.',
 'execution_status':'PROPOSED_ONLY_NOT_EXECUTED'}


def run(output_root, write_docs=False):
    split=load_frozen_split(); train,truth=load_partition_targets(split)
    run_id=datetime.now(timezone.utc).strftime('decision-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
    out=Path(output_root)/run_id; out.mkdir(parents=True,exist_ok=False)
    hashes={}
    def track(p):
        p=Path(p); hashes[str(p)]=sha256(p); return p
    def read(p): return json.loads(track(p).read_text())
    for p in EVIDENCE: track(p)
    for p in OLD.glob('*.csv'): track(p)
    old_receipt=read(OLD/'model_comparison_run_receipt.json')
    for p,h in old_receipt['artifacts_sha256'].items(): require(sha256(track(p))==h, 'Historical diagnostic artifact hash mismatch')
    common={'source_sha256':split.source_sha256,'manifest_id':split.manifest_id,
            'manifest_sha256':split.manifest_sha256,'validation_claim_count':len(truth),'units':'original loss units'}
    base=read(BASELINE); baselines={}; verified_predictions={}; failures=[]
    for r in base['results']:
        path=track(r['prediction_artifact']); require(sha256(path)==r['prediction_sha256'],'Baseline prediction hash mismatch')
        pred=read_predictions(path); score=score_existing(truth,pred,r,split)
        require(pred.prediction.eq(r['fitted_constant']).all(),'Baseline constant mismatch')
        # Audit recorded constants only. Do not calculate/refit new constants.
        require(base['train_claim_count']==len(train),'Baseline training count mismatch')
        baselines[r['baseline_name']]={**common,'verified':True,'validation_mae':score['mae'],
                                      'run_id':base['run_id'],'constant':r['fitted_constant']}
    # Latest Gate 4 reproduction baseline evidence agrees with the original.
    reproduction=read('artifacts/october/gate 4/rerun/reproduction_receipt.json')
    reproduction_base=Path('artifacts/october/gate 4/rerun/baselines')/reproduction['baseline_run_id']
    rb=read(reproduction_base/'baseline_run_receipt.json')
    for r in rb['results']:
        p=track(reproduction_base/Path(r['prediction_artifact']).name)
        require(sha256(p)==r['prediction_sha256'],'Reproduced baseline hash mismatch')
        score=score_existing(truth,read_predictions(p),r,split)
        require(math.isclose(score['mae'],baselines[r['baseline_name']]['validation_mae'],rel_tol=1e-12),'Baseline reproduction disagrees')
    candidates=[]; metrics={}
    glm=read(GLM/'run_receipt.json'); repro_glm=read(G3/'runs/glm-repro-20261110-rachel/reproduction_receipt.json')
    provenance=read(GLM/'provenance.json')
    for name,item in provenance['files'].items(): require(sha256(track(GLM/name))==item['sha256'],'GLM snapshot hash mismatch')
    def evaluate(name,rid,path,evidence,pred_hash,metadata):
        row={**common,'model_name':name,'run_id':rid,'verified':False,'validation_mae':None,**metadata}
        try:
            path=track(path); require(sha256(path)==pred_hash,'Prediction hash mismatch')
            pred=read_predictions(path)
            score=score_existing(truth,pred,evidence,split)
            row.update(verified=True,validation_mae=score['mae'])
            verified_predictions[rid]=pred
        except (ValueError,OSError,KeyError) as exc:
            row['failure_reason']=str(exc); failures.append({'run_id':rid,'reason':str(exc)})
        candidates.append(row)
    require(glm['status']=='completed' and glm['test_used'] is False,'GLM run provenance incomplete')
    evaluate('Ridge GLM',glm['run_id'],GLM/'validation_predictions.csv',glm['validation'],glm['prediction_sha256'],
             {'training_mae':None,'reproduction_training_mae':repro_glm['training_fit_mae'],
              'cross_validation_mae':glm['pooled_cv_mae']['100.0'],'policy_retained':True})
    cv=pd.read_csv(track(GLM/'cv_results.csv')); selected=cv.loc[cv.alpha.eq(100)]
    metrics[glm['run_id']]={'folds':stability(selected.mae.tolist()),'train_metric_scope':'In-sample metric is from the independent reproduction, not the original fit',
                          'training_mae':None,'reproduction_training_mae':repro_glm['training_fit_mae'], 'runtime_seconds':glm['runtime_seconds'], 'runtime_type':'whole search/refit workflow','complexity':'808 encoded inputs; alpha 100'}
    x=read(XGB/'run_receipt.json'); retained=read(G3/'xgboost_results_20261112/retained_model_manifest.json')
    audit=read(G3/'xgboost_results_20261112/results_audit.json')
    require(sha256(XGB/'run_receipt.json')==retained['receipt_sha256']==audit['campaign_receipt_sha256'],'XGBoost receipt hash mismatch')
    for name,h in x['code_sha256'].items(): require(sha256(track(name))==h,'XGBoost fitting/evaluation code hash mismatch')
    require(x['test_partition']=='Never loaded, fitted, tuned, or evaluated' and audit['selection_uses_training_only'] is True,'Training/test provenance incomplete')
    require(x['status']=='COMPLETE' and x['synthetic'] is False and audit['status']=='PASS','XGBoost evidence incomplete')
    for k in ['source_sha256','manifest_sha256']: require(x['frozen_inputs'][k]==getattr(split,k),'XGBoost source/manifest mismatch')
    require(x['config']['inputs']['split_manifest']==split.manifest_id,'XGBoost manifest ID mismatch')
    require(x['config']['target']['transform']=='identity' and x['config']['target']['evaluation_metric']=='MAE in original loss units','XGBoost target scale mismatch')
    require(x['frozen_inputs']['training_claims']==len(train),'XGBoost training population mismatch')
    require(sha256(track(POLICY))==x['readiness']['gate1']['sha256'],'Recorded retention policy changed')
    for k in ['model','preprocessing','validation_predictions']: require(sha256(track(retained[k]['path']))==retained[k]['sha256'],'Retained artifact mismatch')
    improvement=x['comparison']['before_pooled_oof_mae']-x['comparison']['after_pooled_oof_mae']
    keep=improvement>=x['readiness']['minimum_mae_improvement']
    require(keep==x['comparison']['keep_followup']==retained['followup_retained'],'Retention decision inconsistent')
    require(retained['retained_candidate']==x['final_candidate'],'Retained identity inconsistent')
    for label,r in x['releases'].items():
        result=next(v for v in x['results'] if v['id']==r['candidate_id'])
        require(r['status']=='PASS' and result['status']=='PASS','Incomplete release')
        for name,h in r['artifact_sha256'].items(): require(sha256(track(XGB/name))==h,'Release artifact mismatch')
        rid=x['run_id']+':'+r['candidate_id']
        evidence={**common,'evaluated_claim_count':r['claims'],'metric':'MAE','partition':'validation','mae':r['validation_mae']}
        evaluate('XGBoost '+r['candidate_id'],rid,XGB/f'{label}_validation_predictions.csv',evidence,
                 r['artifact_sha256'][f'{label}_validation_predictions.csv'],
                 {'training_mae':None,'cross_validation_mae':result['pooled_oof_mae'],'policy_retained':r['candidate_id']==retained['retained_candidate']})
        metrics[rid]={'folds':stability([f['mae'] for f in result['fold_results']]),'training_mae':None,
                      'runtime_seconds':r['runtime_seconds'],'runtime_type':'release refit/predict/serialization/evaluation',
                      'complexity':f"300 trees, max depth {result['parameters']['max_depth']}; 130 source inputs"}
    # Compare against latest saved comparison rather than the outdated GLM-only table.
    latest=pd.read_csv(track(G3/'xgboost_results_20261112/model_comparison.csv')).set_index('model').validation_mae
    for row,key in zip(candidates,['frozen_glm','xgboost_initial','xgboost_followup']):
        if row['verified']: require(math.isclose(row['validation_mae'],latest[key],rel_tol=1e-12),'Latest comparison disagrees')
    decision=candidate_decision(candidates,baselines,source_sha256=split.source_sha256,manifest_id=split.manifest_id,
                                manifest_sha256=split.manifest_sha256,validation_count=len(truth))
    bins=[]; tails=[]
    for row in candidates:
        if row['verified']:
            b,t,thresholds=diagnostic_summaries(truth,verified_predictions[row['run_id']],train.loss)
            bins.extend(dict(model_name=row['model_name'],run_id=row['run_id'],**v) for v in b)
            tails.extend(dict(model_name=row['model_name'],run_id=row['run_id'],**v) for v in t)
            m=metrics[row['run_id']]; m['validation_minus_cv_fold_mean']=row['validation_mae']-m['folds']['mean_mae']
    pd.DataFrame(bins).to_csv(out/'target_bin_diagnostics.csv',index=False,float_format='%.17g')
    pd.DataFrame(tails).to_csv(out/'high_loss_diagnostics.csv',index=False,float_format='%.17g')
    pd.DataFrame(decision['candidates']).to_csv(out/'october_candidate_decision.csv',index=False,float_format='%.17g')
    (out/'development_evidence.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n')
    decision.update(run_id=run_id,timestamp_utc=datetime.now(timezone.utc).isoformat(),**common,baselines=baselines,
                    selected_candidate=next((r for r in decision['candidates'] if r['run_id']==decision['selected_run_id']),None),
                    diagnostic_references=[str(out/'target_bin_diagnostics.csv'),str(out/'high_loss_diagnostics.csv'),str(out/'development_evidence.json')],
                    evidence_limitations=['Prior full-file EDA; no independent prospective cohort','First-filing availability is an Advisor-authorized assumption, not verified lineage',
                                          'Gate 4 reproduction conditional on Python patch mismatch','No repeated-seed assessment; reproduction is not seed stability',
                                          'GLM narrative differs from machine-readable reproduction receipt; exact numeric assertions use the receipt'],
                    eda_exposure_status='FULL_HISTORICAL_LABELED_DATA_INCLUDING_LATER_VALIDATION_AND_TEST',
                    retrospective_validation_status='HISTORICAL_VALIDATION_ONLY',next_experiment=NEXT,
                    review_status='Generated technical recommendation; team and Challenge Advisor approval not recorded',
                    policy_reference=str(POLICY),failures=failures,
                    code_version=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    (out/'october_candidate_decision.json').write_text(json.dumps(decision,indent=2,allow_nan=False)+'\n')
    if write_docs: write_reports(decision,out,tails,metrics)
    test_code = "import unittest; s=unittest.TestSuite(); [s.addTests(unittest.defaultTestLoader.discover('tests', pattern=p)) for p in ['test_candidate_decision.py','test_model_comparison.py','test_baselines_evaluation.py','test_partition_manifest.py','test_verify_gate2_leng.py']]; r=unittest.TextTestRunner().run(s); raise SystemExit(not r.wasSuccessful())"
    test=subprocess.run([sys.executable,'-c',test_code],capture_output=True,text=True)
    docs=[Path('docs')/name for name in ['october_report.md','october_candidate_decision.md','task_candidate_decision_summary.md']]
    report=docs[0].read_text() if docs[0].exists() else ''
    selected=decision['selected_candidate']
    csv=pd.read_csv(out/'october_candidate_decision.csv',float_precision='round_trip')
    checks={
     'Frozen source verified':sha256(split.source_path)==split.source_sha256,
     'Frozen partition manifest verified':sha256(split.manifest_path)==split.manifest_sha256,
     'Shared MAE evaluator reused':len(verified_predictions)>0,
     'Both constant baselines verified':set(baselines)=={'mean','median'},
     'Candidate prediction coverage verified':not failures,
     'Candidate results evaluated on identical validation claims':all(r['verified'] and r['validation_claim_count']==len(truth) for r in candidates),
     'Original-scale MAE verified':all(r['units']=='original loss units' for r in candidates),
     'Baseline comparison calculations verified':all(not r['verified'] or math.isclose(r['delta_vs_mean'],r['validation_mae']-baselines['mean']['validation_mae']) for r in decision['candidates']),
     'Strict two-baseline selection rule enforced':selected is None or (selected['beats_mean'] and selected['beats_median']),
     'Invalid candidates excluded':selected is None or selected['evaluation_eligibility']=='ELIGIBLE',
     'Candidate decision documented':docs[1].exists(), 'Next experiment documented':bool(decision['next_experiment']['success_criterion']),
     'High-loss diagnostic limitations documented':'high-loss' in report,
     'Overfitting evidence reviewed':all('training_mae' in m for m in metrics.values()),
     'Stability evidence reviewed':all(m['folds']['count']==5 for m in metrics.values()),
     'Prediction failures reviewed':len(candidates)==len(verified_predictions)+len(failures),
     'September EDA exposure documented':'September EDA' in report and 'full labeled' in report,
     'Retrospective validation explicitly stated':'retrospective' in report,
     'First-filing usefulness not overstated':'do not establish' in report,
     'Feature availability limitations documented':'lineage' in report,
     'Internal test isolation during October preserved':set(train.id).union(truth.id).isdisjoint(split.test_ids),
     'Plain-language October report completed':bool(report),
     'Report and decision artifacts consistent':selected is None or (f"{selected['validation_mae']:.6f}" in report and selected['model_name'] in report and len(csv)==len(candidates)),
     'Automated tests passed':test.returncode==0,'Completion summary created':docs[2].exists()}
    receipt={'run_id':run_id,'timestamp_utc':decision['timestamp_utc'],'generation_git_commit':decision['code_version'],
             'git_status_at_generation':subprocess.check_output(['git','status','--porcelain'],text=True),
             'eventual_report_commit':'Not yet available at generation; identify through git history. Code hashes pin generation source.',
             'source_sha256':split.source_sha256,'manifest_id':split.manifest_id,'manifest_sha256':split.manifest_sha256,
             'validation_claim_count':len(truth),'baseline_run_ids':[base['run_id'],rb['run_id']],
             'candidate_run_ids':[r['run_id'] for r in candidates], 'input_sha256':hashes,
             'code_sha256':{p:sha256(p) for p in ['scripts/candidate_report.py','scripts/model_comparison.py','scripts/evaluation.py']},
             'software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
             'reproduction_command':'python3 -m scripts.candidate_report --write-docs',
             'tests':{'scope':'Decision, comparison, shared evaluator, partitions and Gate 2 verification', 'returncode':test.returncode,'output':test.stdout+test.stderr},
             'broader_suite_attempt':{'command':'python3 -m unittest discover -s tests','observed_tests_run':106,'observed_errors':29,'reason':'Existing XGBoost runner tests raise PackageNotFoundError: xgboost in this reporting environment; no unrelated tests changed'},
             'artifact_sha256':{str(p):sha256(p) for p in out.iterdir() if p.is_file()},
             'report_sha256':{str(p):sha256(p) for p in docs if p.exists()}}
    rp=out/'october_report_run_receipt.json'; rp.write_text(json.dumps(receipt,indent=2)+'\n')
    checks['Run receipt generated']=json.loads(rp.read_text())['run_id']==run_id
    receipt['checks']={k:'PASS' if v else 'FAIL' for k,v in checks.items()}
    rp.write_text(json.dumps(receipt,indent=2)+'\n')
    print('October Candidate Decision and Report\n'+'\n'.join(f'- {k}: {v}' for k,v in receipt['checks'].items()))
    print(decision['status'],selected['model_name'] if selected else '',rp)
    require(all(checks.values()),'Report verification failed; inspect receipt')
    return decision


def write_reports(d,out,tails,metrics):
    selected=d['selected_candidate']; chosen=selected['model_name'] if selected else 'None'
    rows=d['candidates']; mean=d['baselines']['mean']['validation_mae']; median=d['baselines']['median']['validation_mae']
    def fmt(value): return 'unavailable' if value is None else f'{value:.6f}'
    table='| Candidate | Validation MAE | Claims | Change vs mean | Change vs median | Improvement vs mean | Improvement vs median | Status |\n|---|---:|---:|---:|---:|---:|---:|---|\n'
    for r in rows:
        table+=f"| {r['model_name']} | {fmt(r['validation_mae'])} | {r['validation_claim_count']} | {fmt(r['delta_vs_mean'])} | {fmt(r['delta_vs_median'])} | {fmt(r['pct_improvement_vs_mean'])}% | {fmt(r['pct_improvement_vs_median'])}% | {r['decision_status']} |\n"
    tail_table='| Candidate | Threshold | Claims / 28,248 | MAE | Mean signed error |\n|---|---:|---:|---:|---:|\n'
    for r in tails:
        if 'p95' in r['tail_label']:
            tail_table+=f"| {r['model_name']} | {r['threshold']:.3f} | {r['claim_count']} | {r['mae']:.2f} | {r['mean_signed_error']:.2f} |\n"
    refs='\n'.join('- `'+str(p)+'`' for p in [BASELINE,GLM/'run_receipt.json',GLM/'provenance.json',XGB/'run_receipt.json',POLICY,G3/'xgboost_results_20261112/model_comparison.csv',OLD/'model_high_loss_diagnostics.csv',out/'october_candidate_decision.json',out/'development_evidence.json'])
    rationale='A2-C03 is the lowest-error policy-retained family candidate and strictly beats both constants. A2-C06 also beats both and has a 0.834209 lower validation MAE, but it failed the adopted training-only retention rule: pooled out-of-fold MAE worsened by 0.409930 instead of improving by at least 1.0. Reversing that decision using validation would reopen the experiment. The Gate 1 across-family one-unit tie proposal was not independently approved globally; no across-family tie affects this result (A2-C03 is 82.938019 below GLM).'
    limits='September EDA examined the full labeled file, including claims later assigned to validation and reserved test. These are retrospective results, not independent prospective confirmation. Filing-time inputs are an Advisor-authorized assumption; individual feature definitions, timestamps and lineage remain unverified. High-loss underprediction persists. Gate 4 reproduction matched predictions exactly but used Python 3.13.2 rather than 3.13.5, so exact environment confirmation remains conditional. Reproductions do not establish random-seed stability.'
    if selected is None:
        text = f"# October candidate decision and report\n\n{d['status']}: {d['rationale']}\n\n{table}\n{limits}\n\nNext experiment: {NEXT}\n\nEvidence: {refs}\n\nReview: technical recommendation only; no team approval.\n"
        for name in ['october_report.md','october_candidate_decision.md','task_candidate_decision_summary.md']:
            Path('docs', name).write_text(text)
        return
    report=f'''# October model development report

## 1. Executive summary

The team investigated whether historical claim characteristics help estimate final paid loss. October milestone work (completed across October and November) established fixed data partitions, two constant benchmarks, a regularized linear model, a boosted-tree model, and a controlled tree-depth follow-up. The technical recommendation is **{d['status']}: {chosen}**, pending team and Challenge Advisor review.

{table}
The retained candidate improves MAE by {selected['pct_improvement_vs_mean']:.2f}% against the mean and {selected['pct_improvement_vs_median']:.2f}% against the median. These results support a provisional research candidate, not demonstrated operational usefulness. {limits}

## 2. Business problem

The research question is whether claim information can help estimate a claim's final cost. This could inform future reserve research, but no improved reserving, handling speed, costs, customer outcomes or compliance has been demonstrated. The supplied population excludes claims closed without payment, so results do not establish performance for all incoming claims.

## 3. Data and evaluation approach

The authoritative historical file contains 188,318 claims and 132 columns: an ID, 116 anonymous categorical predictors, 14 anonymous continuous predictors, and `loss`. ID is a matching key, never a predictor. Split `october-split-v1` fixes 141,238 training, 28,248 validation and 18,832 reserved test claims (75/15/10). Source SHA-256: `{d['source_sha256']}`; manifest SHA-256: `{d['manifest_sha256']}`.

Learned preprocessing and model fitting used training rows; five-fold cross-validation repeatedly held out one fifth of training to compare settings. Saved predictions were joined to validation truth by unique claim ID and independently rescored with the shared evaluator. No baseline was refitted or new model trained for this report. No additional internal test targets were inspected.

Mean absolute error (MAE) measures how far predictions are from recorded claim losses on average, without allowing overpredictions and underpredictions to cancel each other out. All numbers use original loss units; the available field documentation does not establish a currency denomination.

## 4. Baseline results

The training-mean baseline predicts {d['baselines']['mean']['constant']:.6f} for every claim and has validation MAE {mean:.6f}. The training-median comparator predicts {d['baselines']['median']['constant']:.6f} and has MAE {median:.6f}. Both constants were fitted only on training targets, according to their code and receipts, and their saved predictions were verified here. The newer Gate 4 baseline reproduction agrees.

The mean is the average training loss; the median is the middle training loss. A median minimizes absolute error among constant predictions on the fitting population, making it an essential reference. Beating the mean alone is insufficient.

## 5. Candidate models

The Ridge GLM combines encoded features with regularized coefficients to limit overly large effects; it predicts a transformed loss and converts back to original units. Its frozen penalty is 100, with 808 encoded inputs. XGBoost combines 300 small decision trees to capture nonlinear patterns; the retained model has maximum depth 7 and learning rate 0.05. The follow-up changed only depth to 8. The executive table displays rounded results; the decision CSV and JSON retain full-precision values used by the rule.

The previously published November 7 comparison marked XGBoost incomplete. That was correct then; the November 12 committed campaign now supplies its predictions, receipts and audit. This report uses the newer evidence without rewriting historical artifacts.

## 6. Candidate decision

A provisional candidate must have valid evaluation evidence and validation MAE strictly below **both** constants on the exact same claims. A tie with either baseline fails. {rationale}

This is a generated technical recommendation, not a recorded team or Advisor approval. It does not release the test set or authorize deployment. Run IDs and full-precision decision flags are in the formal record.

## 7. Diagnostic findings

{tail_table}
These high-loss slices use the training 95th-percentile threshold, not a threshold chosen from validation results. Negative signed error means underprediction. The 1,403 claims represent 4.97% of validation; the training-p99 slice has 294 claims (1.04%). The latter is a much smaller slice, so conclusions about rare extremes remain limited. Bin tables cover all 28,248 claims and show overprediction toward the low end and underprediction at the high end. Slice diagnostics describe weaknesses; they do not replace overall MAE as the selection metric.

The retained XGBoost CV pooled MAE is 1163.675270; its five fold scores have sample standard deviation 10.600038. Its validation score is about 3.84 above its CV fold mean. No in-sample XGBoost MAE is available, so a true training-to-validation gap cannot be computed. GLM's pooled CV MAE is 1245.404448; the reproduction reports training MAE 1240.423079, with a roughly 10.03 difference from the original validation score. That is a cross-run descriptive comparison, not the original fit's exact generalization gap. These small differences do not prove absence of overfitting.

Rachel's GLM reproduction receipt reports near-identical predictions (maximum difference about 3.64e-12); the narrative record uses looser bounds and attributes variation to solver tolerance. We use the machine-readable receipt for exact numeric assertions. Hector's XGBoost reproduction matches saved predictions and model bytes but has the Python patch mismatch described above. Reproduction agreement is distinct from random-seed or prospective stability; no repeated-seed assessment exists.

All three released candidate prediction files passed coverage, numeric and recorded-score checks; no rows were repaired or dropped. XGBoost reports zero campaign failures/retries. GLM's 89-second measurement covers its whole search/refit workflow; XGBoost's 294.80-second campaign covers 30 CV fits and two releases, with 198.31 seconds of recorded fitting compute. These workloads and environments differ, so runtime does not support a fair speed ranking.

## 8. September EDA exposure

September EDA used the **full labeled historical dataset** before the split was frozen. In `notebooks/data-understanding.ipynb`, zero-based cell 5 loads the full CSV; zero-based cells 15, 34 and 48 inspect loss and predictor-target relationships without an October partition filter. Saved September target, categorical and continuous summaries and the Recommendation Register confirm that findings informed the later preprocessing, model-family and diagnostic plans.

Thus later validation and reserved-test observations and targets had already contributed to exploration. Training-only preprocessing does not erase that exposure. Three issues must be distinguished: (1) direct fitting leakage, for which the reviewed code/receipts enforce training-only boundaries and do not establish a violation; (2) prior exploratory exposure, which is established; and (3) repeated validation-based selection, whose risk grows with reuse. GLM and two XGBoost releases, baseline scoring, diagnostics and reproduction audits reuse the validation population. Rescoring fixed predictions is not a new experiment, but neither does it create independent evidence.

The reserved test remained uninspected during this report and October modeling according to receipts, but it is not historically unseen. Its future authorized evaluation cannot undo September exposure. Genuinely independent data is needed for stronger confirmation.

## 9. Retrospective validation and filing-time use

The October results provide retrospective evidence of predictive performance on historical claims. They **do not establish** reliable or useful estimates at first filing, because availability and timing of individual anonymized predictors have not been independently verified.

The Advisor's October 12 written response, documented in Gate 1 signoff (the recommendation register uses October 13), permits assuming fields are available at filing/model use. This is a project assumption, not verified field-by-field lineage or timestamps. Some historical fields could have been recorded or updated after filing; this is a potential risk, not proof of post-filing leakage.

Future claims may differ in mix, inflation, repair costs, underwriting or reporting processes. Those are potential distribution-shift risks, not observed findings in this evaluation. Independent or temporally separated data, defined prediction/outcome timestamps, prospective validation and an operational workflow assessment are needed before usefulness can be established.

## 10. Responsible use and next confirmation

Unknown field meanings and group/time structure limit interpretation, dependence checks and fairness assessment. Anonymization does not establish fairness or remove all privacy concerns. No evidence here supports claims of bias-free behavior, compliance, production readiness, or automated claim/payment decisions. Business success criteria and appropriate governance, fairness and privacy review must precede operational use.

Proposed next test: {NEXT['change']} Hypothesis: {NEXT['hypothesis']} Controls: {NEXT['controls']} Success criterion: {NEXT['success_criterion']} Dependencies: {NEXT['dependencies']} Risks: {NEXT['risks']} This proposal was not executed. Exact Python-version reproduction remains a separate team prerequisite; it was not rerun here because that would refit a model.

## Verification scope

All 80 relevant decision, evaluator, comparison, partition and Gate 2 verification tests pass, including 19 new decision tests. The broader repository suite was attempted (106 tests) but produced 29 error entries in existing XGBoost-runner tests because `xgboost` is not installed in the reporting interpreter. This report evaluates saved predictions using pandas/NumPy; it does not claim an exact training environment or a passing full training-workflow suite. No unrelated tests or environments were changed.

## Evidence and reproduction

{refs}

Generated run: `{d['run_id']}`. Reproduce verification and documents with `python3 -m scripts.candidate_report --write-docs`. Run decision tests with `python3 -m unittest discover -s tests -p test_candidate_decision.py`. The receipt records input, report and decision hashes, actual library versions, generation Git revision and dirty-tree state separately from the eventual report commit.
'''
    Path('docs/october_report.md').write_text(report)
    formal=f'''# October candidate decision

Status: **{d['status']}**. Provisional candidate: **{chosen}**.

{d['rationale']}. Review status: {d['review_status']}.

## Rule and evidence

Strictly lower original-scale validation MAE than both constants on the same 28,248 IDs from `october-split-v1`; invalid predictions/provenance are excluded. Source and manifest hashes, baseline identities and all candidate run IDs are in the machine-readable record.

{table}
{rationale}

Candidate runs:

'''+ '\n'.join(f"- {r['model_name']}: `{r['run_id']}`; evaluation {r['evaluation_eligibility']}." for r in rows)+f'''

Baseline run: `{d['baselines']['mean']['run_id']}`. Diagnostic concerns:

{tail_table}
{limits}

No in-sample XGBoost error or repeated-seed evidence exists. Fold variability and reproduction findings are documented in the October report. All released predictions pass integrity checks; the follow-up is evaluation-eligible but not retained under the approved policy.

## Next confirmation

'''+ '\n'.join(f'- **{k.replace("_"," ")}**: {v}' for k,v in NEXT.items())+f'''

## Evidence references

{refs}

Full explanation: [October report](october_report.md). Decision JSON: `{out/'october_candidate_decision.json'}`. No team/Advisor approval is inferred; the next experiment is proposed, not executed.
'''
    Path('docs/october_candidate_decision.md').write_text(formal)
    Path('docs/task_candidate_decision_summary.md').write_text(f'''# Candidate decision and October report completion

Verified existing baseline and candidate predictions using the shared evaluator and exact frozen validation IDs. Added reusable strict two-baseline decision logic with synthetic tests, reviewed the pre-recorded XGBoost retention policy, refreshed diagnostics for all released candidates, and generated a stakeholder report and formal technical recommendation.

Decision: **{d['status']} — {chosen}**.

{table}
{limits}

The GLM-only comparison is historical, not current. All candidate releases now have valid evidence. A2-C06 remains non-retained under the training-CV policy despite its slightly lower validation score. The GLM reproduction narrative and receipt differ in their precision; this report uses receipt values and labels cross-run training evidence.

Next confirmation: {NEXT['change']} Success criterion: {NEXT['success_criterion']} Team/Advisor review, independent data, feature lineage and exact-environment reproduction remain open; no approval is fabricated.

Files: `scripts/model_comparison.py` (decision helper); `scripts/candidate_report.py`; `tests/test_candidate_decision.py`; `docs/october_report.md`; `docs/october_candidate_decision.md`; this summary; decision CSV/JSON, target-bin/high-loss CSVs, development evidence JSON and report receipt under `{out}`.

Reproduce: `python3 -m scripts.candidate_report --write-docs`. Synthetic tests: `python3 -m unittest discover -s tests -p test_candidate_decision.py`. The run receipt contains the computed validation checklist, tests and exact hashes. Generation code version is distinct from the eventual commit containing these outputs.

All 80 relevant decision, comparison, evaluator, partition and Gate 2 verification tests pass (including 19 new decision tests); the broader 106-test repository run encountered 29 error entries from the missing `xgboost` dependency in existing runner tests. This limitation is separate from the report's verified prediction results.

No new candidate models trained, baseline constants refitted, hyperparameters tuned, partition assignments changed, additional internal test targets inspected, or production-readiness claims made.
''')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-root',type=Path,default=Path('artifacts/october/gate 4/candidate_decision'))
    p.add_argument('--write-docs',action='store_true')
    a=p.parse_args(); run(a.output_root,a.write_docs)
