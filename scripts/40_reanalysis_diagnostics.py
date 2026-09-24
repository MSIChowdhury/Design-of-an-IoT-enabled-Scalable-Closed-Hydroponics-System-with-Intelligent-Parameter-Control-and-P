"""Evaluate validation-maximum-coverage settings for otherwise infeasible arms.

These are diagnostics, not settings that passed the prespecified coverage targets.
Selection uses validation only and is saved before evaluation.
"""
from pathlib import Path
from dataclasses import replace
import runpy

import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.reanalysis import Timing, authorize, hold_estimate, score_actions, summarize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/metrics/reanalysis'


def main():
    helpers = runpy.run_path(str(ROOT / 'scripts/38_replay_reanalysis.py'))
    cfg = load_yaml(ROOT / 'configs/experiments/reanalysis.yaml')
    base = load_aasvr_config(ROOT / 'configs/methods/aasvr.yaml')
    validation = pd.read_csv(OUT / 'validation_operating_points.csv')
    selections = pd.read_csv(OUT / 'locked_validation_selections.csv')
    evaluated = set(selections.loc[selections.status == 'selected','method']) | {'always_deny'}
    choices = []
    for method, group in validation[validation.deadline == cfg['selection_deadline_seconds']].groupby('method'):
        if method in evaluated:
            continue
        if method not in ('aasvr_measurement','aasvr_no_cusum'):
            raise ValueError('Diagnostic replay needs a detector model for ' + method)
        best = group.sort_values(['coverage','undesirable_per_trial','setting'],
                                 ascending=[False,True,True]).iloc[0]
        choices.append({'method':method,'setting':best.setting,'validation_coverage':best.coverage,
                        'status':'diagnostic_only_coverage_target_not_met'})
    pd.DataFrame(choices).to_csv(OUT / 'diagnostic_validation_selections.csv',index=False)
    frame = pd.read_parquet(ROOT / 'data/processed/hydro_exp1_measurements.parquet').sort_values('timestamp').reset_index(drop=True)
    windows = pd.read_csv(OUT / 'source_windows.csv')
    rows, traces = [], []
    timing = Timing(persistence=cfg['reference_persistence_seconds'],cooldown=cfg['cooldown_seconds'],
                    max_gap=cfg['max_gap_seconds'])
    for wi, window in enumerate(windows[windows.split == 'evaluation'].itertuples()):
        sub = frame.iloc[window.start:window.end]
        times = (sub.timestamp-sub.timestamp.iloc[0]).dt.total_seconds().to_numpy()
        for sensor in (s for s in base.sensors if s.name in cfg['sensors']):
            for kind in cfg['scenarios']:
                background, corrupted, labels = helpers['scenario'](sub[sensor.name].to_numpy(),kind,
                    cfg['magnitudes'][sensor.name],cfg['warmup_samples'],cfg['fault_samples'])
                trial_id = f'{window.window_id}_{sensor.name}_{kind}'
                for choice in choices:
                    multiplier,persistence,max_age = [float(x[1:]) for x in choice['setting'].split('_')]
                    accepted, gate = helpers['detector'](choice['method'],corrupted,times,sensor,base,multiplier,None)
                    estimate, age = hold_estimate(times,corrupted,accepted,max_gap=timing.max_gap)
                    actions = authorize(times,estimate,gate & (age <= max_age),sensor.control_low,sensor.control_high,
                                        replace(timing,persistence=persistence,max_age=max_age))
                    for deadline in cfg['deadlines_seconds']:
                        metrics = score_actions(times,background,corrupted,accepted,actions,sensor.control_low,sensor.control_high,
                            timing=replace(timing,max_age=max_age),deadline=deadline,
                            start=times[cfg['warmup_samples']],stop=times[-1]-max(cfg['deadlines_seconds']),
                            fault_labels=labels,held=(estimate,age))
                        rows.append({**choice,'trial_id':trial_id,'source_day':window.source_day,
                                     'window_id':window.window_id,'sensor':sensor.name,'scenario':kind,
                                     'deadline':deadline,**metrics})
                    if wi == 0 and sensor.name == 'pH' and kind in ('spike_positive','bias_positive','legitimate_positive'):
                        traces.extend({'trial_id':trial_id,'scenario':kind,**choice,'seconds':t,
                                       'background':b,'corrupted':c,'estimate':e,'accepted':a,'age_seconds':ag,'action':ac}
                            for t,b,c,e,a,ag,ac in zip(times,background,corrupted,estimate,accepted,age,actions))
        print(f'Diagnostic evaluation window {wi+1} complete',flush=True)
    detail = pd.DataFrame(rows)
    detail.to_csv(OUT / 'diagnostic_evaluation_detail.csv',index=False)
    report = []
    for (method,setting,deadline),group in detail.groupby(['method','setting','deadline']):
        report.append({'method':method,'setting':setting,'deadline':deadline,
                       'status':'diagnostic_only_coverage_target_not_met',**summarize(group)})
    pd.DataFrame(report).to_csv(OUT / 'diagnostic_evaluation_summary.csv',index=False)
    pd.DataFrame(traces).to_csv(OUT / 'diagnostic_example_traces.csv',index=False)


if __name__ == '__main__':
    main()
