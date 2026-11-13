"""Actions forecast-service accepts."""
from enum import Enum


class ForecastAction(str, Enum):
    FORECAST = "FORECAST"     # read only: the forecast per place and product for the next days, with history and accuracy
    SNAPSHOT = "SNAPSHOT"     # keep today's and tomorrow's forecast (once per day) to check it against what happened
