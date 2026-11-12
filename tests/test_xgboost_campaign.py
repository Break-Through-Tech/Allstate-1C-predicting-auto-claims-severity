"""Training-only depth choices for the approved campaign controller."""
import unittest
from scripts.evaluation import EvaluationError
from scripts.run_xgboost_campaign import recommend_depth


def receipt(winner, rows):
    return {'stage': 'INITIAL_COMPLETE', 'initial_winner': winner, 'releases': {},
            'results': [{'id': name, 'parameters': {'max_depth': depth, 'learning_rate': rate},
                         'pooled_oof_mae': mae, 'validation_mae': -1000000}
                        for name, depth, rate, mae in rows]}


class CampaignTests(unittest.TestCase):
    def test_untested_depth_follows_training_evidence_at_selected_rate(self):
        rows = [('a', 3, .05, 30.), ('b', 5, .05, 20.), ('c', 7, .05, 10.),
                ('d', 3, .1, 11.), ('e', 5, .1, 10.)]
        for winner, expected in [('a', 2), ('c', 8), ('e', 6)]:
            with self.subTest(winner=winner):
                plan = recommend_depth(receipt(winner, rows))
                self.assertEqual(plan['value'], expected)
                self.assertNotIn(plan['value'], {3, 5, 7})
                self.assertEqual(plan['parameter'], 'max_depth')
                self.assertTrue(all(x['id'] in ({'a', 'b', 'c'} if winner != 'e' else {'d', 'e'}) for x in plan['evidence']))

    def test_interior_depth_uses_better_neighbor_and_shallower_tie(self):
        for left, right, expected in [(21., 25., 4), (25., 21., 6), (21., 21., 4)]:
            data = receipt('b', [('a', 3, .05, left), ('b', 5, .05, 20.), ('c', 7, .05, right)])
            self.assertEqual(recommend_depth(data)['value'], expected)

    def test_validation_release_prevents_late_recommendation(self):
        data = receipt('a', [('a', 3, .05, 20.), ('b', 5, .05, 21.)])
        data['releases']['initial'] = {'validation_mae': 1.}
        with self.assertRaises(EvaluationError): recommend_depth(data)


if __name__ == '__main__':
    unittest.main()
