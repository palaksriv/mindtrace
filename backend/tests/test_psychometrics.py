"""Reliability helpers used by the pilot-study analysis scripts."""

import math

import numpy as np
import pytest

from app.services.psychometrics import (
    bootstrap_ci,
    cronbach_alpha,
    pearson_r,
    retest_correlation,
    spearman_brown,
)


def test_alpha_matches_a_hand_computed_example() -> None:
    # 4 respondents x 3 items. Item variances (ddof=1): 1.6667, 1.6667, 1.6667; totals 6,9,12,15 -> var 15
    data = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6]]
    # alpha = 3/2 * (1 - 5/15) = 1.0 exactly because items are perfectly correlated
    assert cronbach_alpha(data) == pytest.approx(1.0)


def test_alpha_is_low_for_unrelated_items() -> None:
    rng = np.random.default_rng(1)
    assert abs(cronbach_alpha(rng.normal(size=(400, 4)))) < 0.15


def test_alpha_is_high_for_correlated_items() -> None:
    rng = np.random.default_rng(2)
    latent = rng.normal(size=(300, 1))
    assert cronbach_alpha(latent + 0.5 * rng.normal(size=(300, 4))) > 0.85


def test_alpha_undefined_cases_return_nan() -> None:
    assert math.isnan(cronbach_alpha([[1, 2]]))
    assert math.isnan(cronbach_alpha([[1], [2], [3]]))
    assert math.isnan(cronbach_alpha([[3, 3], [3, 3], [3, 3]]))


def test_spearman_brown_doubling() -> None:
    assert spearman_brown(0.5, 2) == pytest.approx(2 / 3)
    assert spearman_brown(0.7, 1) == pytest.approx(0.7)
    with pytest.raises(ValueError):
        spearman_brown(0.5, 0)


def test_pearson_and_retest() -> None:
    assert pearson_r([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert retest_correlation([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert math.isnan(pearson_r([1, 1, 1], [1, 2, 3]))


def test_bootstrap_ci_brackets_the_point_estimate() -> None:
    rng = np.random.default_rng(3)
    data = rng.normal(size=(200, 1)) + 0.6 * rng.normal(size=(200, 4))
    lo, hi = bootstrap_ci(cronbach_alpha, data, n_boot=300)
    assert lo <= cronbach_alpha(data) <= hi
