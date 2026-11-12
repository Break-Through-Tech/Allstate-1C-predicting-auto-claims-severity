import copy,json,pathlib,tempfile,types
from contextlib import contextmanager
from unittest.mock import patch
from scripts import run_xgboost as r

pathlib.Path('/private/tmp/task4-runner-audit').mkdir(exist_ok=True)
report={}
original_lock=r.locked
config=json.loads((r.ROOT/r.CONFIG).read_text())
readiness={'release_sequence':'amend_to_one_release','minimum_mae_improvement':1.,
           'deadline_utc':'2099-01-01T00:00:00+00:00','max_runtime_seconds':1000}
context,training,folds=r.synthetic_inputs()

def fixture():
 return {'synthetic':False,'config_sha256':r.sha256(r.ROOT/r.CONFIG),'code_sha256':r.code_hashes(),
         'readiness':readiness,'stage':'FOLLOWUP_FROZEN','cv_fits_attempted':25,
         'configurations_attempted':5,'results':[{'status':'PASS'}],'releases':{}}

with tempfile.TemporaryDirectory() as d:
 output=pathlib.Path(d)
 rec=fixture()
 r.write_json(output/'run_receipt.json',rec)
 @contextmanager
 def finish_other_writer_then_lock(path):
  completed=copy.deepcopy(rec)
  completed.update(stage='COMPLETE',cv_fits_attempted=30,configurations_attempted=6)
  r.write_json(path/'run_receipt.json',completed)
  with original_lock(path): yield
 observed={}
 def record_followup(path, loaded, *args):
  observed.update(in_memory_stage=loaded['stage'],in_memory_cv_fits=loaded['cv_fits_attempted'],
                  disk_stage=json.loads((path/'run_receipt.json').read_text())['stage'],
                  disk_cv_fits=json.loads((path/'run_receipt.json').read_text())['cv_fits_attempted'])
 with patch.object(r,'CAMPAIGN',output),patch.object(r,'check_readiness',return_value=readiness),\
      patch.object(r,'locked',finish_other_writer_then_lock),\
      patch.object(r,'real_inputs',return_value=(context,training,folds)),\
      patch.object(r,'followup',side_effect=record_followup):
  r.main(['followup'])
 report['stale_receipt_race']=observed
 assert observed['in_memory_cv_fits']==25 and observed['disk_cv_fits']==30

with tempfile.TemporaryDirectory() as d:
 output=pathlib.Path(d)
 rec=fixture();rec['versions']={'xgboost':'DIFFERENT_FROM_CURRENT_ENVIRONMENT'}
 r.write_json(output/'run_receipt.json',rec)
 with patch.object(r,'CAMPAIGN',output),patch.object(r,'check_readiness',return_value=readiness),\
      patch.object(r,'real_inputs',return_value=(context,training,folds)),\
      patch.object(r,'followup') as followup:
  r.main(['followup'])
 report['version_drift_not_rejected']=followup.called
 assert followup.called

# Audit a real synthetic release without fitting a model: capture the shared
# evaluator's inputs and use a lightweight estimator/preprocessor double.
with tempfile.TemporaryDirectory() as d:
 output=pathlib.Path(d)
 captured={}
 class Prep:
  named_steps={'native':types.SimpleNamespace(rare_levels_={},categories_={})}
  def fit_transform(self,x): return x
  def transform(self,x): return x
 class Model:
  def __init__(self,**kwargs): pass
  def fit(self,x,y): pass
  def predict(self,x):
   captured['validation_features_equal_training_first_row']=x.reset_index(drop=True).equals(training[r.FEATURES].iloc[:1].reset_index(drop=True))
   return r.np.array([1.])
  def save_model(self,path):pathlib.Path(path).write_text('{}')
  def load_model(self,path):pass
 rec={'stage':'FOLLOWUP_COMPLETE','results':[{'id':'A2-C01','status':'PASS','parameters':{}}],
      'releases':{},'readiness':readiness,'fit_runtime_seconds':0,'final_candidate':'A2-C01'}
 original_evaluate=r.evaluate_mae
 def capture(truth,pred,**kwargs):
  captured['validation_truth_equals_training_first_row']=float(truth.loss.iloc[0])==float(training.loss.iloc[0])
  captured['validation_id']=int(truth.id.iloc[0])
  return original_evaluate(truth,pred,**kwargs)
 with patch.dict('sys.modules',{'xgboost':types.SimpleNamespace(XGBRegressor=Model)}),\
      patch.object(r,'load_preprocessor',return_value=Prep()),patch.object(r,'evaluate_mae',side_effect=capture):
  r.release(output,rec,config,context,training,synthetic=True)
 report['synthetic_validation_relabels_training_row']=captured
 assert captured['validation_truth_equals_training_first_row']
 assert captured['validation_features_equal_training_first_row']

pathlib.Path('/private/tmp/task4-runner-audit/probe_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
