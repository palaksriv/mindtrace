"""Unit tests for the behavioural analytics and trait scoring rules.

Telemetry is simulated with lightweight stand-ins because the analytics only
read attributes; this keeps the tests fast and deterministic.
"""

import random
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pytest

from app.services.analytics.behavior_analytics import (
    DEFAULT_CONFIG,
    calculate_behavioral_analytics,
)
from app.services.scoring import calculate_trait_scores
from app.models.assessment import Trait


def make_samples(seed, n=600, p_face=0.99, p_ch=0.93, p_cv=0.92, yaw=4, pitch=6, roll=3, p_blink=0.06, hz=2.0):
    r = random.Random(seed)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    for i in range(n):
        at = t0 + timedelta(seconds=i / hz)
        if r.random() >= p_face:
            out.append(NS(recorded_at=at, face_detected=False, left_ear=0, right_ear=0, blink_detected=False,
                          gaze_direction="unknown", head_yaw=0, head_pitch=0, head_roll=0))
            continue
        h = "center" if r.random() < p_ch else r.choice(["left", "right"])
        v = "center" if r.random() < p_cv else r.choice(["up", "down"])
        ear = r.gauss(0.62, 0.05)
        out.append(NS(recorded_at=at, face_detected=True, left_ear=ear, right_ear=ear, blink_detected=r.random() < p_blink,
                      gaze_direction=f"{h}-{v}", head_yaw=r.gauss(0, yaw), head_pitch=r.gauss(0, pitch), head_roll=r.gauss(0, roll)))
    return out


SCENARIOS = {
    "A": dict(seed=1, p_face=0.99, p_ch=0.93, p_cv=0.92, yaw=4, pitch=6, roll=3),
    "B": dict(seed=2, p_face=0.70, p_ch=0.85, p_cv=0.85, yaw=6, pitch=9, roll=4),
    "C": dict(seed=3, p_face=0.97, p_ch=0.40, p_cv=0.45, yaw=14, pitch=28, roll=18),
}


def test_steady_session_is_low_with_no_cues() -> None:
    a = calculate_behavioral_analytics(make_samples(**SCENARIOS["A"]))
    assert a["behavioral_deviation"]["level"] == "LOW"
    assert a["behavioral_deviation"]["signals"] == ["No major behavioral deviations were observed."]
    assert a["data_quality"]["status"] == "ok"


def test_intermittent_face_presence_raises_only_the_presence_cue() -> None:
    a = calculate_behavioral_analytics(make_samples(**SCENARIOS["B"]))
    assert a["face_presence_percent"] < 80
    assert a["behavioral_deviation"]["signals"] == ["Face presence was inconsistent during the session."]


def test_off_centre_session_raises_gaze_and_movement_cues() -> None:
    a = calculate_behavioral_analytics(make_samples(**SCENARIOS["C"]))
    signals = " ".join(a["behavioral_deviation"]["signals"])
    assert "Gaze was frequently directed away" in signals
    assert "head movement" in signals
    assert a["behavioral_deviation"]["level"] == "MODERATE"


def test_deviation_index_matches_the_published_formula() -> None:
    a = calculate_behavioral_analytics(make_samples(**SCENARIOS["C"]))
    g = a["gaze_distribution"]
    gaze_term = ((100 - g["horizontal"]["center"]) + (100 - g["vertical"]["center"])) / 2
    expected = 0.30 * (100 - a["face_presence_percent"]) + 0.35 * gaze_term + 0.35 * a["head_movement"]["movement_score"]
    assert a["behavioral_deviation"]["score"] == pytest.approx(expected, abs=0.02)


def test_empty_telemetry_is_unavailable_not_low() -> None:
    a = calculate_behavioral_analytics([])
    assert a["data_quality"]["status"] == "no_telemetry"
    assert a["behavioral_deviation"]["level"] == "UNAVAILABLE"
    assert "unavailable" in a["behavioral_deviation"]["signals"][0]


def test_sparse_sessions_are_flagged() -> None:
    a = calculate_behavioral_analytics(make_samples(seed=9, n=10))
    assert a["data_quality"]["status"] == "sparse"
    assert any("Very few" in s for s in a["behavioral_deviation"]["signals"])


def test_effective_sampling_rate_and_blinks_per_minute_use_timestamps() -> None:
    samples = make_samples(seed=4, n=241, p_face=1.0, p_blink=0.0, hz=2.0)  # 120 s
    for i in range(0, 241, 24):  # exactly 11 blink events
        samples[i].blink_detected = True
    a = calculate_behavioral_analytics(samples)
    assert a["data_quality"]["effective_sampling_hz"] == pytest.approx(2.0, abs=0.01)
    assert a["data_quality"]["duration_seconds"] == pytest.approx(120.0)
    assert a["blink_rate_per_minute"] == pytest.approx(11 / 2, abs=0.01)


def test_center_both_percent_counts_samples_centred_on_both_axes() -> None:
    s = make_samples(seed=5, n=4, p_face=1.0)
    for item, d in zip(s, ["center-center", "center-up", "left-center", "center-center"]):
        item.gaze_direction = d
    assert calculate_behavioral_analytics(s)["gaze_distribution"]["center_both_percent"] == 50.0


def test_thresholds_are_configurable_for_calibration() -> None:
    samples = make_samples(**SCENARIOS["C"])
    strict = replace(DEFAULT_CONFIG, moderate_from=10.0, high_from=20.0)
    assert calculate_behavioral_analytics(samples, config=strict)["behavioral_deviation"]["level"] == "HIGH"


def test_default_weights_sum_to_one() -> None:
    c = DEFAULT_CONFIG
    assert c.yaw_weight + c.pitch_weight + c.roll_weight == pytest.approx(1.0)
    assert c.face_weight + c.gaze_weight + c.movement_weight == pytest.approx(1.0)


def test_latency_statistics() -> None:
    responses = [NS(question_id=i, latency_ms=ms) for i, ms in enumerate([1000, 2000, 3000], start=1)]
    lat = calculate_behavioral_analytics([], responses)["response_latency"]
    assert (lat["minimum_latency_ms"], lat["maximum_latency_ms"], lat["average_latency_ms"]) == (1000, 3000, 2000.0)


# ---------------------------------------------------------------- trait scoring

def _responses(value_fn):
    """Build 20 stand-in responses: 5 traits x (2 forward, 2 reverse)."""
    out = []
    for trait in Trait:
        for reverse in (False, True, False, True):
            q = NS(trait=trait, reverse_scored=reverse)
            out.append(NS(question=q, response=value_fn(trait, reverse)))
    return out


@pytest.mark.parametrize("c", [1, 2, 3, 4, 5])
def test_straight_lining_yields_a_flat_profile_of_60(c: int) -> None:
    scores = calculate_trait_scores(_responses(lambda t, r: c))
    assert set(scores.values()) == {60.0}


def test_scores_span_20_to_100() -> None:
    high = calculate_trait_scores(_responses(lambda t, r: 1 if r else 5))
    low = calculate_trait_scores(_responses(lambda t, r: 5 if r else 1))
    assert set(high.values()) == {100.0} and set(low.values()) == {20.0}
