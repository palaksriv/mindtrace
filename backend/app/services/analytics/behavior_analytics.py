from collections import Counter
from dataclasses import dataclass
from statistics import mean, pstdev

from app.models.assessment import BehaviorTelemetry, Response


@dataclass(frozen=True)
class AnalyticsConfig:
    """Every heuristic weight and threshold in one place.

    These values are design choices that have NOT yet been calibrated against
    real sessions (see docs/PILOT_PROTOCOL.md). Keeping them in a single
    immutable object makes calibration and sensitivity analysis explicit and
    lets tests exercise alternative settings without editing the algorithm.
    """

    # Head-movement normalisation: standard deviation (degrees) that maps to 100.
    yaw_reference_deg: float = 20.0
    pitch_reference_deg: float = 40.0
    roll_reference_deg: float = 25.0
    # Movement score weights (sum to 1).
    yaw_weight: float = 0.35
    pitch_weight: float = 0.40
    roll_weight: float = 0.25
    # Deviation index weights (sum to 1).
    face_weight: float = 0.30
    gaze_weight: float = 0.35
    movement_weight: float = 0.35
    # Level cut-offs on the 0-100 deviation index.
    moderate_from: float = 30.0
    high_from: float = 60.0
    # Cue thresholds.
    min_face_presence_percent: float = 80.0
    min_center_gaze_percent: float = 50.0
    movement_cue_from: float = 60.0
    # Data-quality: fewer samples than this (30 s at 2 Hz) is flagged as sparse.
    min_reliable_samples: int = 60


DEFAULT_CONFIG = AnalyticsConfig()


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(mean(values), 4)


def _safe_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0

    return round(pstdev(values), 4)


def _percentage(part: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round((part / total) * 100, 2)


def _classify_deviation(score: float, config: AnalyticsConfig = DEFAULT_CONFIG) -> str:
    if score < config.moderate_from:
        return "LOW"

    if score < config.high_from:
        return "MODERATE"

    return "HIGH"


def _calculate_data_quality(
    telemetry: list[BehaviorTelemetry],
    config: AnalyticsConfig,
) -> dict:
    """Describe how much telemetry exists so that absence is never silent."""
    count = len(telemetry)
    if count == 0:
        return {
            "status": "no_telemetry",
            "sample_count": 0,
            "duration_seconds": 0.0,
            "effective_sampling_hz": 0.0,
        }

    stamps = [
        item.recorded_at
        for item in telemetry
        if getattr(item, "recorded_at", None) is not None
    ]
    duration = (
        (max(stamps) - min(stamps)).total_seconds() if len(stamps) >= 2 else 0.0
    )
    hz = round((count - 1) / duration, 3) if duration > 0 else 0.0
    return {
        "status": "sparse" if count < config.min_reliable_samples else "ok",
        "sample_count": count,
        "duration_seconds": round(duration, 2),
        "effective_sampling_hz": hz,
    }


def _calculate_response_latency(
    responses: list[Response],
) -> dict:
    if not responses:
        return {
            "response_count": 0,
            "average_latency_ms": 0.0,
            "minimum_latency_ms": 0,
            "maximum_latency_ms": 0,
            "latency_variation_ms": 0.0,
            "per_question": [],
        }

    latency_values = [
        response.latency_ms
        for response in responses
        if response.latency_ms >= 0
    ]

    if not latency_values:
        return {
            "response_count": 0,
            "average_latency_ms": 0.0,
            "minimum_latency_ms": 0,
            "maximum_latency_ms": 0,
            "latency_variation_ms": 0.0,
            "per_question": [],
        }

    per_question = [
        {
            "question_id": response.question_id,
            "latency_ms": response.latency_ms,
        }
        for response in responses
    ]

    return {
        "response_count": len(latency_values),
        "average_latency_ms": _safe_mean(
            latency_values
        ),
        "minimum_latency_ms": min(
            latency_values
        ),
        "maximum_latency_ms": max(
            latency_values
        ),
        "latency_variation_ms": _safe_std(
            latency_values
        ),
        "per_question": per_question,
    }


def _split_gaze_direction(
    direction: str | None,
) -> tuple[str, str]:
    if not direction:
        return "unknown", "unknown"

    parts = direction.strip().lower().split("-", 1)

    if len(parts) != 2:
        return "unknown", "unknown"

    horizontal = parts[0]
    vertical = parts[1]

    valid_horizontal = {
        "left",
        "center",
        "right",
    }

    valid_vertical = {
        "up",
        "center",
        "down",
    }

    if horizontal not in valid_horizontal:
        horizontal = "unknown"

    if vertical not in valid_vertical:
        vertical = "unknown"

    return horizontal, vertical


def _calculate_gaze_distribution(
    telemetry: list[BehaviorTelemetry],
) -> dict:
    horizontal_counter = Counter()
    vertical_counter = Counter()

    for item in telemetry:
        horizontal, vertical = _split_gaze_direction(
            item.gaze_direction
        )

        horizontal_counter[horizontal] += 1
        vertical_counter[vertical] += 1

    total_samples = len(telemetry)

    horizontal_distribution = {
        "center": _percentage(
            horizontal_counter.get("center", 0),
            total_samples,
        ),
        "left": _percentage(
            horizontal_counter.get("left", 0),
            total_samples,
        ),
        "right": _percentage(
            horizontal_counter.get("right", 0),
            total_samples,
        ),
        "unknown": _percentage(
            horizontal_counter.get("unknown", 0),
            total_samples,
        ),
    }

    vertical_distribution = {
        "center": _percentage(
            vertical_counter.get("center", 0),
            total_samples,
        ),
        "up": _percentage(
            vertical_counter.get("up", 0),
            total_samples,
        ),
        "down": _percentage(
            vertical_counter.get("down", 0),
            total_samples,
        ),
        "unknown": _percentage(
            vertical_counter.get("unknown", 0),
            total_samples,
        ),
    }

    return {
        "horizontal": horizontal_distribution,
        "vertical": vertical_distribution,
    }


def _calculate_head_movement(
    telemetry: list[BehaviorTelemetry],
    config: AnalyticsConfig = DEFAULT_CONFIG,
) -> dict:
    if len(telemetry) < 2:
        return {
            "yaw_variation": 0.0,
            "pitch_variation": 0.0,
            "roll_variation": 0.0,
            "movement_score": 0.0,
        }

    yaw_values = [
        item.head_yaw
        for item in telemetry
    ]

    pitch_values = [
        item.head_pitch
        for item in telemetry
    ]

    roll_values = [
        item.head_roll
        for item in telemetry
    ]

    yaw_variation = _safe_std(yaw_values)
    pitch_variation = _safe_std(pitch_values)
    roll_variation = _safe_std(roll_values)

    # Convert raw angular variation into normalized
    # movement contributions.
    #
    # These reference ranges represent increasing
    # amounts of observable movement rather than
    # psychological interpretation.
    yaw_score = min(
        100.0,
        (yaw_variation / config.yaw_reference_deg) * 100.0,
    )

    pitch_score = min(
        100.0,
        (pitch_variation / config.pitch_reference_deg) * 100.0,
    )

    roll_score = min(
        100.0,
        (roll_variation / config.roll_reference_deg) * 100.0,
    )

    movement_score = (
        yaw_score * config.yaw_weight
        + pitch_score * config.pitch_weight
        + roll_score * config.roll_weight
    )

    movement_score = round(
        min(100.0, movement_score),
        2,
    )

    return {
        "yaw_variation": yaw_variation,
        "pitch_variation": pitch_variation,
        "roll_variation": roll_variation,
        "movement_score": movement_score,
    }


def _both_center_percent(telemetry: list[BehaviorTelemetry]) -> float:
    """Share of face-present samples with BOTH gaze axes labelled centre."""
    if not telemetry:
        return 0.0
    both = sum(
        1
        for item in telemetry
        if _split_gaze_direction(item.gaze_direction) == ("center", "center")
    )
    return _percentage(both, len(telemetry))


def calculate_behavioral_analytics(
    telemetry: list[BehaviorTelemetry],
    responses: list[Response] | None = None,
    config: AnalyticsConfig = DEFAULT_CONFIG,
) -> dict:
    responses = responses or []
    data_quality = _calculate_data_quality(telemetry, config)

    response_latency = _calculate_response_latency(
        responses
    )

    if not telemetry:
        return {
            "sample_count": 0,
            "data_quality": data_quality,
            "face_presence_percent": 0.0,
            "blink_rate": 0.0,
            "blink_rate_per_minute": 0.0,
            "average_ear": 0.0,
            "response_latency": response_latency,
            "gaze_distribution": {
                "horizontal": {
                    "center": 0.0,
                    "left": 0.0,
                    "right": 0.0,
                    "unknown": 0.0,
                },
                "vertical": {
                    "center": 0.0,
                    "up": 0.0,
                    "down": 0.0,
                    "unknown": 0.0,
                },
                "center_both_percent": 0.0,
            },
            "head_movement": {
                "yaw_variation": 0.0,
                "pitch_variation": 0.0,
                "roll_variation": 0.0,
                "movement_score": 0.0,
            },
            # No data is reported as UNAVAILABLE, never as a calm LOW session.
            "behavioral_deviation": {
                "score": 0.0,
                "level": "UNAVAILABLE",
                "signals": [
                    "No camera telemetry was captured; behavioural "
                    "indicators are unavailable for this session."
                ],
            },
        }

    total_samples = len(telemetry)

    valid_face_samples = [
        item
        for item in telemetry
        if item.face_detected
    ]

    face_presence_percent = _percentage(
        len(valid_face_samples),
        total_samples,
    )

    average_ear = _safe_mean(
        [
            (
                item.left_ear
                + item.right_ear
            ) / 2
            for item in valid_face_samples
        ]
    )

    blink_events = sum(
        1
        for item in telemetry
        if item.blink_detected
    )

    blink_rate = round(
        blink_events / total_samples,
        4,
    )

    gaze_distribution = _calculate_gaze_distribution(
        valid_face_samples
    )
    gaze_distribution["center_both_percent"] = _both_center_percent(
        valid_face_samples
    )

    head_movement = _calculate_head_movement(
        valid_face_samples,
        config,
    )

    movement_score = head_movement[
        "movement_score"
    ]

    center_horizontal = gaze_distribution[
        "horizontal"
    ]["center"]

    center_vertical = gaze_distribution[
        "vertical"
    ]["center"]

    gaze_deviation = (
        (
            (100.0 - center_horizontal)
            + (100.0 - center_vertical)
        )
        / 2.0
    )

    face_deviation = max(
        0.0,
        100.0 - face_presence_percent,
    )

    movement_deviation = movement_score

    deviation_score = min(
        100.0,
        round(
            (
                face_deviation * config.face_weight
                + gaze_deviation * config.gaze_weight
                + movement_deviation * config.movement_weight
            ),
            2,
        ),
    )

    signals: list[str] = []

    if data_quality["status"] == "sparse":
        signals.append(
            "Very few telemetry samples were captured; interpret the "
            "indicators with caution."
        )

    if face_presence_percent < config.min_face_presence_percent:
        signals.append(
            "Face presence was inconsistent during the session."
        )

    if (
        center_horizontal < config.min_center_gaze_percent
        or center_vertical < config.min_center_gaze_percent
    ):
        signals.append(
            "Gaze was frequently directed away from the center."
        )

    if movement_score >= config.movement_cue_from:
        signals.append(
            "Noticeable head movement variation was observed."
        )

    if not any(s for s in signals if not s.startswith("Very few")):
        signals.append(
            "No major behavioral deviations were observed."
        )

    duration_minutes = data_quality["duration_seconds"] / 60.0
    blink_rate_per_minute = (
        round(blink_events / duration_minutes, 2) if duration_minutes > 0 else 0.0
    )

    return {
        "sample_count": total_samples,
        "data_quality": data_quality,
        "face_presence_percent": face_presence_percent,
        "blink_rate": blink_rate,
        "blink_rate_per_minute": blink_rate_per_minute,
        "average_ear": average_ear,
        "response_latency": response_latency,
        "gaze_distribution": gaze_distribution,
        "head_movement": head_movement,
        "behavioral_deviation": {
            "score": deviation_score,
            "level": _classify_deviation(
                deviation_score,
                config,
            ),
            "signals": signals,
        },
    }