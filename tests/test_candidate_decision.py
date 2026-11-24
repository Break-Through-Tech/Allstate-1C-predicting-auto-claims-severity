import copy
import math
import unittest
from scripts.model_comparison import candidate_decision

class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.context = dict(source_sha256='a'*64, manifest_id='split-v1', manifest_sha256='b'*64, validation_count=3)
        self.row = dict(source_sha256='a'*64, manifest_id='split-v1', manifest_sha256='b'*64,
                        validation_claim_count=3, verified=True, units='original loss units', run_id='A', model_name='A', validation_mae=5.)
        self.baselines = {'mean': dict(self.row, validation_mae=10.), 'median': dict(self.row, validation_mae=8.)}
    def decide(self, rows=None):
        return candidate_decision([self.row] if rows is None else rows, self.baselines, **self.context)
    def test_beats_both(self): self.assertEqual(self.decide()['status'], 'PROVISIONAL_CANDIDATE')
    def test_only_mean(self):
        self.row['validation_mae']=9.; self.assertEqual(self.decide()['status'],'NO_SELECTION')
    def test_only_median(self):
        self.baselines['mean']['validation_mae']=4.; self.assertEqual(self.decide()['status'],'NO_SELECTION')
    def test_neither(self):
        self.row['validation_mae']=11.; self.assertEqual(self.decide()['status'],'NO_SELECTION')
    def test_tie_mean(self):
        self.row['validation_mae']=10.; self.assertEqual(self.decide()['status'],'NO_SELECTION')
    def test_tie_median(self):
        self.row['validation_mae']=8.; self.assertEqual(self.decide()['status'],'NO_SELECTION')
    def test_multiple(self):
        self.assertEqual(self.decide([self.row,dict(self.row,run_id='B',validation_mae=4.)])['selected_run_id'],'B')
    def test_invalid_coverage(self):
        self.row['verified']=False; self.assertEqual(self.decide()['status'],'INSUFFICIENT_EVIDENCE')
    def test_manifest(self):
        self.row['manifest_id']='other'; self.assertEqual(self.decide()['status'],'INSUFFICIENT_EVIDENCE')
    def test_source(self):
        self.row['source_sha256']='other'; self.assertEqual(self.decide()['status'],'INSUFFICIENT_EVIDENCE')
    def test_invalid_mae(self):
        for value in [None,math.nan,math.inf,-math.inf,-1]:
            self.row['validation_mae']=value
            with self.subTest(value=value): self.assertEqual(self.decide()['status'],'INSUFFICIENT_EVIDENCE')
    def test_baselines(self):
        for value in [None,math.nan,-1]:
            self.baselines['mean']['validation_mae']=value
            self.assertEqual(self.decide()['status'],'INSUFFICIENT_EVIDENCE')
        self.baselines={}; self.assertEqual(self.decide()['status'],'INSUFFICIENT_EVIDENCE')
    def test_no_models(self): self.assertEqual(self.decide([])['status'],'INSUFFICIENT_EVIDENCE')
    def test_full_precision(self):
        self.row['validation_mae']=7.99999999
        self.assertEqual(round(self.row['validation_mae'],2),8.)
        self.assertEqual(self.decide()['status'],'PROVISIONAL_CANDIDATE')
    def test_diagnostics_do_not_override(self):
        self.row.update(validation_mae=9., high_loss_mae=0.,runtime_seconds=0.)
        self.assertEqual(self.decide()['status'],'NO_SELECTION')
    def test_reproducible(self): self.assertEqual(self.decide(),self.decide())
    def test_nonretained(self):
        result=self.decide([self.row,dict(self.row,run_id='B',validation_mae=4.,policy_retained=False)])
        self.assertEqual(result['selected_run_id'],'A')
        self.assertEqual(result['candidates'][1]['decision_status'],'NOT_RETAINED_BY_EXISTING_POLICY')
    def test_numerical_tie(self):
        self.assertEqual(self.decide([self.row,dict(self.row,run_id='B')])['status'],'INSUFFICIENT_EVIDENCE')
    def test_no_input_mutation(self):
        before=copy.deepcopy(self.row); self.decide(); self.assertEqual(before,self.row)

if __name__=='__main__': unittest.main()
