from __future__ import annotations

from pathlib import Path

import pandas as pd

LABEL_COLUMNS = [
    "timestamp",
    "dataset",
    "event_id",
    "sensor",
    "fault",
    "fault_type",
    "severity",
    "label_source",
    "confidence",
]

EVENT_COLUMNS = [
    "event_id",
    "dataset",
    "sensor",
    "start_time",
    "end_time",
    "event_type",
    "confidence",
    "evidence",
    "severity",
    "manual_intervention",
    "actuator_affected",
    "notes",
]


def normalize_labels(labels: pd.DataFrame | None) -> pd.DataFrame:
    if labels is None or labels.empty:
        return pd.DataFrame(columns=LABEL_COLUMNS)
    out = labels.copy()
    for column in LABEL_COLUMNS:
        if column not in out:
            out[column] = _default_value(column)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce", utc=True)
    out["fault"] = out["fault"].astype(bool)
    out["confidence"] = pd.to_numeric(out["confidence"], errors="coerce").fillna(0.0)
    return out[LABEL_COLUMNS].dropna(subset=["timestamp"]).reset_index(drop=True)


def labels_from_events(events: pd.DataFrame, measurements: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=LABEL_COLUMNS)
    required = {"event_id", "dataset", "sensor", "start_time", "end_time", "event_type"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"Manual event annotations are missing columns: {missing}")

    measured = measurements.copy()
    measured["timestamp"] = pd.to_datetime(measured["timestamp"], errors="coerce", utc=True)
    rows = []
    for event in events.itertuples(index=False):
        start = pd.to_datetime(event.start_time, errors="coerce", utc=True)
        end = pd.to_datetime(event.end_time, errors="coerce", utc=True)
        if pd.isna(start) or pd.isna(end):
            continue
        sensor = str(event.sensor)
        dataset = str(event.dataset)
        mask = (measured["timestamp"] >= start) & (measured["timestamp"] <= end)
        sensors = _event_sensors(sensor, measured)
        timestamps = measured.loc[mask, "timestamp"]
        confidence = getattr(event, "confidence", 1.0)
        severity = getattr(event, "severity", "manual")
        for sensor_name in sensors:
            for timestamp in timestamps:
                rows.append(
                    {
                        "timestamp": timestamp,
                        "dataset": dataset,
                        "event_id": str(event.event_id),
                        "sensor": sensor_name,
                        "fault": True,
                        "fault_type": str(event.event_type),
                        "severity": str(severity),
                        "label_source": "manual_event",
                        "confidence": float(confidence) if pd.notna(confidence) else 1.0,
                    }
                )
    return normalize_labels(pd.DataFrame(rows))


def load_manual_events(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=EVENT_COLUMNS)
    events = pd.read_csv(path)
    for column in EVENT_COLUMNS:
        if column not in events:
            events[column] = ""
    return events[EVENT_COLUMNS]


def merge_label_sources(*labels: pd.DataFrame) -> pd.DataFrame:
    frames = [normalize_labels(frame) for frame in labels if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame(columns=LABEL_COLUMNS)
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values(["timestamp", "sensor", "confidence"], ascending=[True, True, False])
    return merged.drop_duplicates(["timestamp", "dataset", "sensor", "fault_type"], keep="first").reset_index(
        drop=True
    )


def event_template_from_decisions(decisions: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty or "timestamp" not in decisions or "sensor" not in decisions:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    frame = decisions.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    flagged = frame[
        frame.get("gate_result", pd.Series("", index=frame.index)).eq("reject")
        | frame.get("alert", pd.Series(False, index=frame.index)).astype(bool)
    ].dropna(subset=["timestamp"])
    rows = []
    event_id = 0
    for sensor, sensor_frame in flagged.sort_values("timestamp").groupby("sensor"):
        current_start = None
        current_end = None
        previous_time = None
        for row in sensor_frame.itertuples(index=False):
            timestamp = row.timestamp
            if current_start is None:
                current_start = timestamp
                current_end = timestamp
            elif previous_time is not None and (timestamp - previous_time).total_seconds() <= 60:
                current_end = timestamp
            else:
                event_id += 1
                rows.append(_event_row(event_id, sensor, current_start, current_end))
                current_start = timestamp
                current_end = timestamp
            previous_time = timestamp
        if current_start is not None:
            event_id += 1
            rows.append(_event_row(event_id, sensor, current_start, current_end))
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def _event_row(event_id: int, sensor: str, start: pd.Timestamp, end: pd.Timestamp) -> dict[str, object]:
    return {
        "event_id": f"candidate_{event_id}",
        "dataset": "hydro_exp1",
        "sensor": sensor,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "event_type": "review_candidate",
        "confidence": 0.5,
        "evidence": "AASVR reject/alert candidate",
        "severity": "possible",
        "manual_intervention": "",
        "actuator_affected": "",
        "notes": "",
    }


def _event_sensors(sensor: str, measurements: pd.DataFrame) -> list[str]:
    if sensor in {"*", "all"}:
        return [
            column
            for column in measurements.columns
            if column not in {"timestamp", "dataset", "split", "entry_id"}
        ]
    return [sensor] if sensor in measurements.columns else []


def _default_value(column: str) -> object:
    if column == "fault":
        return False
    if column == "confidence":
        return 0.0
    return ""
