"""Action routing for forecast-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import ForecastAction
from . import forecast
from . import snapshot

TABLE = "forecast_requests"
ROUTES = {
    ForecastAction.FORECAST: forecast.handle,
    ForecastAction.SNAPSHOT: snapshot.handle,
}
handle = ActionDispatcher(ROUTES, ForecastAction, TABLE)
