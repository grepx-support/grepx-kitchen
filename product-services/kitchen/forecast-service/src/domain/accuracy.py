# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""How good a method is: WAPE (total error / total sold, in %) on the last week of history, forecast from the weeks
before it. Lower is better; None when there is not enough history to test. Pure."""
from __future__ import annotations

from datetime import date

from .methods import METHODS, Method

HOLDOUT = 7


def wape(actual: list[float], predicted: list[float]) -> float | None:
    total = sum(actual)
    if total <= 0:
        return None
    return round(sum(abs(a - p) for a, p in zip(actual, predicted)) * 100 / total, 1)


def backtest(history: list[tuple[date, float]], method: Method, holdout: int = HOLDOUT) -> float | None:
    train, test = history[:-holdout], history[-holdout:]
    if len(train) < 7 or len(test) < holdout:
        return None
    return wape([q for _, q in test], method.predict(train, [d for d, _ in test]))


def best(history: list[tuple[date, float]]) -> tuple[str, dict[str, float | None]]:
    """The most accurate method for this history (the weekday one when none can be tested) and every score."""
    scores = {key: backtest(history, m) for key, m in METHODS.items()}
    tested = {k: v for k, v in scores.items() if v is not None}
    return (min(tested, key=tested.get) if tested else "weekday"), scores
