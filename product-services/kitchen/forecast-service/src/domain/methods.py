# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Forecasting methods (Strategy): each takes the history - [(date, qty)], oldest first - and the days to forecast, and
returns a quantity per day. New methods only need a class here and a place in METHODS. Pure."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from statistics import mean


class Method(ABC):
    key = ""
    label = ""

    @abstractmethod
    def predict(self, history: list[tuple[date, float]], days: list[date]) -> list[float]:
        """One quantity (>= 0) per day asked for."""


class MovingAverage(Method):
    """Every day like the average of the last week."""
    key, label = "moving_average", "Last 7 days average"

    def __init__(self, window: int = 7):
        self.window = window

    def predict(self, history, days):
        recent = [q for _, q in history[-self.window:]]
        level = mean(recent) if recent else 0.0
        return [level for _ in days]


class SameWeekday(Method):
    """Each day like the same weekday over the last four weeks (Fridays like Fridays); the weekly average when a
    weekday has no history yet."""
    key, label = "weekday", "Same weekday, last 4 weeks"

    def __init__(self, weeks: int = 4):
        self.weeks, self.fallback = weeks, MovingAverage()

    def predict(self, history, days):
        out = []
        for day in days:
            same = [q for d, q in history if d.weekday() == day.weekday()][-self.weeks:]
            out.append(mean(same) if same else self.fallback.predict(history, [day])[0])
        return out


class TrendWeekday(Method):
    """The straight-line trend of the last four weeks, times each weekday's usual share: for products growing or
    fading. Never below zero."""
    key, label = "trend", "Trend with weekday pattern"

    def predict(self, history, days):
        recent = history[-28:]
        if len(recent) < 7:
            return SameWeekday().predict(history, days)
        xs, ys = list(range(len(recent))), [q for _, q in recent]
        x0, y0 = mean(xs), mean(ys)
        spread = sum((x - x0) ** 2 for x in xs) or 1.0
        slope = sum((x - x0) * (y - y0) for x, y in zip(xs, ys)) / spread
        fit = [y0 + slope * (x - x0) for x in xs]
        factor = self._weekday_factors(recent, fit)
        last = recent[-1][0]
        return [max(0.0, (y0 + slope * (len(recent) - 1 - x0 + (d - last).days)) * factor.get(d.weekday(), 1.0)) for d in days]

    @staticmethod
    def _weekday_factors(recent, fit: list[float]) -> dict[int, float]:
        """Each weekday's usual share against the trend line (so growth is not mistaken for a strong weekday)."""
        by_day: dict[int, list[float]] = {}
        for (d, q), f in zip(recent, fit):
            if f > 0:
                by_day.setdefault(d.weekday(), []).append(q / f)
        return {wd: mean(r) for wd, r in by_day.items()}


METHODS: dict[str, Method] = {m.key: m for m in (MovingAverage(), SameWeekday(), TrendWeekday())}
