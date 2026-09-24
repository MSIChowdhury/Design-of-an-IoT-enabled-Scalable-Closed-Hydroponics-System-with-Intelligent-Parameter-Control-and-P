"""Independent, elapsed-time authorization scoring for retrospective replay.

The background is a surrogate, not physical ground truth. No replay action
changes that background. Legacy scoring and AASVR-R behavior are left intact.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Timing:
    persistence: float = 32.0
    cooldown: float = 600.0
    max_gap: float = 120.0
    max_age: float = 64.0


def directions(values, low: float, high: float) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    return np.where(np.isfinite(x), np.where(x < low, 1, np.where(x > high, -1, 0)), 0)


def hold_estimate(times, values, accepted, *, max_gap=120.0):
    """Record age since actual acceptance; a gap invalidates the held value."""
    estimate = np.full(len(times), np.nan)
    age = np.full(len(times), np.inf)
    last = np.nan
    last_time = -np.inf
    for i, t in enumerate(times):
        if i and t - times[i - 1] > max_gap:
            last, last_time = np.nan, -np.inf
        if accepted[i] and np.isfinite(values[i]):
            last, last_time = values[i], t
        estimate[i], age[i] = last, t - last_time
    return estimate, age


def authorize(times, estimate, eligible, low, high, timing=Timing()):
    """One pulse per eligible opportunity; cooldown is measured in seconds.

    Direction persistence accumulates during cooldown. Gaps reset persistence,
    but never shorten an outstanding cooldown. Eligibility loss resets it too.
    """
    direction = directions(estimate, low, high)
    actions = np.zeros(len(times), dtype=int)
    since, previous, next_allowed = None, 0, -np.inf
    for i, t in enumerate(times):
        d = int(direction[i]) if eligible[i] else 0
        gap = bool(i and t - times[i - 1] > timing.max_gap)
        if not d:
            since, previous = None, 0
            continue
        if since is None or d != previous or gap:
            since = t
        previous = d
        if t - since >= timing.persistence and t >= next_allowed:
            actions[i] = d
            next_allowed = t + timing.cooldown
    return actions


def reference_trace(times, background, low, high, timing=Timing()):
    """Episodes and recurring opportunities are defined independently of methods."""
    direction = directions(background, low, high)
    episode = np.full(len(times), -1, dtype=int)
    current = -1
    for i, d in enumerate(direction):
        if not d:
            continue
        if i == 0 or d != direction[i - 1] or times[i] - times[i - 1] > timing.max_gap:
            current += 1
        episode[i] = current
    actions = authorize(times, background, np.isfinite(background), low, high, timing)
    return direction, episode, actions


def score_actions(times, background, corrupted, accepted, actions, low, high,
                  *, timing=Timing(), deadline=180.0, start=0.0, stop=None,
                  fault_labels=None, held=None):
    """One-to-one, same-episode/direction matching within a fixed deadline.

    Eligible slots recur at reference cooldown intervals. A matching action
    cannot serve two slots or cross the next slot. Slots beyond stop are not
    scored; the observed tail remains available for delayed matching. Caller
    must retain at least deadline seconds of follow-up after stop.
    """
    times = np.asarray(times, dtype=float)
    stop = times[-1] - deadline if stop is None else stop
    if stop + deadline > times[-1] + 1e-8:
        raise ValueError("Insufficient deadline follow-up")
    direction, episode, reference = reference_trace(times, background, low, high, timing)
    mask = (times >= start) & (times <= stop)
    slots_all = np.flatnonzero(reference)
    slots = slots_all[mask[slots_all]]
    used, matched, delays = set(), [], []
    for i in slots:
        later = slots_all[slots_all > i]
        end = min(times[i] + deadline, times[later[0]] if len(later) else np.inf)
        candidates = np.flatnonzero((times >= times[i]) & (times <= end)
                                   & (episode == episode[i]) & (actions == reference[i]))
        # The next slot owns an action exactly at its eligibility timestamp.
        if len(later):
            candidates = candidates[candidates < later[0]]
        hit = next((int(j) for j in candidates if int(j) not in used), None)
        if hit is not None:
            used.add(hit)
            matched.append(int(i))
            delays.append(times[hit] - times[i])
    authorized = (np.asarray(actions) != 0) & mask
    wrong = authorized & (direction != 0) & (actions != direction)
    unnecessary = authorized & (direction == 0)
    fault = (~np.isfinite(corrupted) & np.isfinite(background)) | (
        np.isfinite(corrupted) & np.isfinite(background)
        & ~np.isclose(corrupted, background, rtol=0, atol=1e-12))
    if fault_labels is not None:
        fault = np.asarray(fault_labels, dtype=bool)
    estimate, age = held if held is not None else hold_estimate(
        times, corrupted, accepted, max_gap=timing.max_gap)
    valid = mask & np.isfinite(estimate) & np.isfinite(background)
    episodes = set(episode[slots])
    served_episodes = set(episode[matched])
    finite_age = age[mask & np.isfinite(age)]
    fault_indices = np.flatnonzero(fault & mask)
    detected = fault_indices[~np.asarray(accepted)[fault_indices]]
    recovery = np.nan
    all_fault = np.flatnonzero(fault)
    if len(all_fault) and all_fault[-1] + 1 < len(times):
        end = all_fault[-1] + 1
        recovered = np.flatnonzero(np.asarray(accepted)[end:])
        if len(recovered):
            recovery = times[end + recovered[0]] - times[end]
    last_accepted = np.maximum.accumulate(np.where(accepted, np.arange(len(times)), -1))
    held_fault = (last_accepted >= 0) & fault[np.maximum(last_accepted, 0)]
    return {
        "opportunities": len(slots), "matched": len(matched),
        "episodes": len(episodes), "served_episodes": len(served_episodes),
        "zero_opportunity_trials": int(not len(slots)),
        "authorizations": int(authorized.sum()), "wrong_direction": int(wrong.sum()),
        "unnecessary": int(unnecessary.sum()),
        "fault_evidence": int((authorized & fault).sum()),
        "held_fault_evidence": int((authorized & held_fault).sum()),
        "delay_sum_seconds": float(sum(delays)),
        "age_sum_seconds": float(finite_age.sum()), "age_observations": len(finite_age),
        "max_age_seconds": float(finite_age.max()) if len(finite_age) else np.nan,
        "uninitialized_samples": int((mask & ~np.isfinite(age)).sum()),
        "stale_samples": int((mask & (age > timing.max_age)).sum()),
        "scored_samples": int(mask.sum()),
        "absolute_error_sum": float(np.abs(estimate[valid] - np.asarray(background)[valid]).sum()),
        "estimate_samples": int(valid.sum()),
        "fault_samples": int((fault & mask).sum()),
        "detected_fault_samples": len(detected),
        "clean_samples": int((~fault & mask).sum()),
        "rejected_clean_samples": int((~fault & mask & ~np.asarray(accepted)).sum()),
        "fault_event": int(len(fault_indices) > 0),
        "detected_event": int(len(detected) > 0),
        "detection_delay_seconds": float(times[detected[0]] - times[fault_indices[0]])
            if len(detected) else np.nan,
        "recovery_seconds": recovery,
        "recovery_censored": int(len(all_fault) > 0 and not np.isfinite(recovery)),
    }


def summarize(frame):
    """Pool explicit numerators and denominators, never average undefined rates."""
    def ratio(a, b):
        denominator = frame[b].sum()
        return float(frame[a].sum() / denominator) if denominator else np.nan
    return {
        "trials": len(frame), "opportunities": int(frame.opportunities.sum()),
        "zero_opportunity_trials": int(frame.zero_opportunity_trials.sum()),
        "coverage": ratio("matched", "opportunities"),
        "episode_coverage": ratio("served_episodes", "episodes"),
        "undesirable_per_trial": float((frame.unnecessary + frame.wrong_direction).mean()),
        "unnecessary_per_trial": float(frame.unnecessary.mean()),
        "wrong_direction_per_trial": float(frame.wrong_direction.mean()),
        "fault_evidence_per_trial": float(frame.fault_evidence.mean()),
        "held_fault_evidence_per_trial": float(frame.held_fault_evidence.mean()),
        "authorizations_per_trial": float(frame.authorizations.mean()),
        "delay_seconds": ratio("delay_sum_seconds", "matched"),
        "mean_age_seconds": ratio("age_sum_seconds", "age_observations"),
        "stale_fraction": ratio("stale_samples", "scored_samples"),
        "sample_recall": ratio("detected_fault_samples", "fault_samples"),
        "clean_rejection_rate": ratio("rejected_clean_samples", "clean_samples"),
        "event_recall": ratio("detected_event", "fault_event"),
        "recovery_censored_fraction": float(frame.loc[frame.fault_event > 0,
                                                        "recovery_censored"].mean()),
    }
