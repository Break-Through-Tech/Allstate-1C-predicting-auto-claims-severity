"""Run the approved staged CLI without retries; retain progress and provenance."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from scripts import run_xgboost as r


def recommend_depth(receipt):
    """Consume initial training CV only, before any validation release exists."""
    r.require(receipt['stage'] == 'INITIAL_COMPLETE' and not receipt['releases'],
              'Depth recommendation requires initial CV before validation release')
    parent = next(x for x in receipt['results'] if x['id'] == receipt['initial_winner'])
    rate, depth = parent['parameters']['learning_rate'], parent['parameters']['max_depth']
    evidence = sorted([{'id': x['id'], 'depth': x['parameters']['max_depth'],
                        'pooled_oof_mae': x['pooled_oof_mae']}
                       for x in receipt['results'] if x['parameters']['learning_rate'] == rate],
                      key=lambda x: x['depth'])
    if depth == evidence[0]['depth']:
        proposed = max(1, depth - 1)
        reason = 'The shallowest depth was selected; test one step shallower to assess whether simpler trees improve training OOF MAE.'
    elif depth == evidence[-1]['depth']:
        proposed = depth + 1
        reason = 'The deepest depth at this learning rate was selected; test one deeper level for additional nonlinear structure.'
    else:
        neighbors = [x for x in evidence if x['depth'] != depth]
        neighbor = min(neighbors, key=lambda x: (x['pooled_oof_mae'], x['depth']))
        proposed = (depth + neighbor['depth']) // 2
        reason = 'The selected depth is interior; interpolate toward the neighboring depth with lower training OOF MAE, preferring shallower on a tie.'
    r.require(proposed not in {x['parameters']['max_depth'] for x in receipt['results']},
              'Recommended depth was already tested')
    rationale = (f"Initial training-only evidence at learning_rate={rate}: "
                 + '; '.join(f"{x['id']} depth {x['depth']} pooled OOF MAE {x['pooled_oof_mae']:.12f}" for x in evidence)
                 + f". Parent {parent['id']} uses depth {depth}. {reason} Change only max_depth to {proposed}; all other settings stay fixed. Validation is not an input.")
    return {'parent': parent['id'], 'parameter': 'max_depth', 'old_value': depth, 'value': proposed,
            'learning_rate': rate, 'evidence': evidence, 'rationale': rationale,
            'frozen_before_validation_utc': r.now()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readiness', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    config = json.loads((r.ROOT / r.CONFIG).read_text())
    readiness = r.check_readiness(config, args.readiness)
    r.check_environment(config, r.actual_environment())
    r.require(readiness['release_sequence'] == 'gate1_two_releases', 'This controller requires the approved two-release sequence')
    r.require(not (r.ROOT / r.CAMPAIGN).exists(), 'Campaign already exists; automatic retry/reset is disabled')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    print(f'Campaign log: {output / "campaign.log"}', flush=True)
    state = {'started_utc': r.now(), 'git_commit': r.git('rev-parse', 'HEAD'),
             'controller_sha256': r.sha256(Path(__file__)), 'runner_sha256': r.code_hashes(),
             'readiness_sha256': r.sha256(args.readiness), 'config_sha256': r.sha256(r.ROOT / r.CONFIG),
             'status': 'RUNNING', 'steps': [], 'first_real_fit_verified': False}
    start = time.monotonic()
    receipt_path = r.ROOT / r.CAMPAIGN / 'run_receipt.json'
    with (output / 'campaign.log').open('x', buffering=1) as log:
        def say(message):
            print(f'{r.now()} {message}', file=log, flush=True)

        def save():
            r.write_json(output / 'automation_receipt.json', state)

        def run_step(stage, extra=()):
            command = [sys.executable, '-u', '-B', '-m', 'scripts.run_xgboost', stage,
                       '--readiness', str(args.readiness), *extra]
            entry = {'stage': stage, 'command': command, 'started_utc': r.now(), 'status': 'RUNNING'}
            state['steps'].append(entry)
            save()
            say(f'STAGE_START {stage}')
            process = subprocess.Popen(command, cwd=r.ROOT, stdout=log, stderr=subprocess.STDOUT)
            entry['pid'] = process.pid
            save()
            signature = None
            while True:
                if receipt_path.exists():
                    current = json.loads(receipt_path.read_text())
                    completed = sum(len(x['fold_results']) for x in current['results'])
                    observed = (current['stage'], current['cv_fits_attempted'], completed,
                                len(current['releases']), current['status'])
                    if observed != signature:
                        say(f'PROGRESS stage={observed[0]} CV_attempts={observed[1]}/30 completed_folds={completed} validation_attempts={observed[3]} status={observed[4]}')
                        signature = observed
                    if not state['first_real_fit_verified'] and completed > 0 and current['synthetic'] is False:
                        state['first_real_fit_verified'] = True
                        state['first_real_fit_verified_utc'] = r.now()
                        say('FIRST_REAL_FIT_VERIFIED: at least one real CV fit completed and its held-out score was saved.')
                        save()
                code = process.poll()
                if code is not None:
                    break
                time.sleep(2)
            entry.update(exit_code=code, ended_utc=r.now(), status='PASS' if code == 0 else 'FAILED')
            save()
            r.require(code == 0, f'{stage} failed; no automatic retry. Inspect {output / "campaign.log"}')
            say(f'STAGE_END {stage} PASS')

        try:
            run_step('initial')
            recommendation = recommend_depth(json.loads(receipt_path.read_text()))
            path = output / 'depth_recommendation.json'
            r.write_json(path, recommendation, new=True)
            state['depth_recommendation_sha256'] = r.sha256(path)
            save()
            say(f"DEPTH_FROZEN_BEFORE_VALIDATION parent={recommendation['parent']} new_max_depth={recommendation['value']}")
            run_step('release')
            r.require(r.sha256(path) == state['depth_recommendation_sha256'], 'Depth recommendation changed')
            run_step('freeze-followup', ['--parameter', 'max_depth', '--value', str(recommendation['value']),
                                         '--rationale', recommendation['rationale']])
            run_step('followup')
            run_step('release')
            state['status'] = 'COMPLETE'
            say('CAMPAIGN_COMPLETE: independently audit saved predictions before reporting final MAE.')
        except BaseException as exc:
            state.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
            say(state['error'])
            raise
        finally:
            state.update(ended_utc=r.now(), elapsed_seconds=time.monotonic() - start)
            save()


if __name__ == '__main__':
    main()
