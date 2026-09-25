"""Psychometric reliability and validity helpers for pilot-study analysis.

These functions are deliberately dependency-light (NumPy only) and are used by
``scripts/reliability_report.py``. They make it possible to report internal
consistency, test-retest stability and convergent validity as soon as real
response data exist.
"""

from __future__ import annotations

import numpy as np


def _matrix(scores: list[list[float]] | np.ndarray) -> np.ndarray:
    arr = np.asarray(scores, dtype=float)
    if arr.ndim != 2:
        raise ValueError("scores must be a 2-D array: respondents x items")
    return arr


def cronbach_alpha(scores: list[list[float]] | np.ndarray) -> float:
    """Cronbach's alpha for a respondents x items matrix of *keyed* scores.

    Reverse-keyed items must already have been reversed. Returns ``nan`` when
    alpha is undefined (fewer than two items or respondents, or zero total
    variance).
    """
    arr = _matrix(scores)
    n_respondents, k_items = arr.shape
    if k_items < 2 or n_respondents < 2:
        return float("nan")
    item_var = arr.var(axis=0, ddof=1).sum()
    total_var = arr.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return float("nan")
    return float(k_items / (k_items - 1) * (1 - item_var / total_var))


def spearman_brown(reliability: float, length_factor: float) -> float:
    """Predicted reliability if a scale is lengthened by ``length_factor``."""
    if length_factor <= 0:
        raise ValueError("length_factor must be positive")
    return float(length_factor * reliability / (1 + (length_factor - 1) * reliability))


def pearson_r(x: list[float] | np.ndarray, y: list[float] | np.ndarray) -> float:
    """Pearson correlation; ``nan`` if either input has zero variance."""
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if a.shape != b.shape or a.size < 3:
        return float("nan")
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def retest_correlation(first: list[float], second: list[float]) -> float:
    """Test-retest stability for one trait: correlation of two administrations."""
    return pearson_r(first, second)


def bootstrap_ci(
    statistic,
    data: np.ndarray,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap CI for ``statistic(resampled_rows)``."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(data)
    values = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(arr), len(arr))
        v = statistic(arr[idx])
        if not np.isnan(v):
            values.append(v)
    if not values:
        return float("nan"), float("nan")
    lo, hi = np.percentile(values, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)
