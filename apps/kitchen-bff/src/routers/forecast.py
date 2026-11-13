# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sales forecasts (forecast-service) for the kitchen screen, and turning them into this week's production targets
(planning-service SET_TARGET, one per product). The BFF only passes the request on and checks who may do it."""
import math

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/forecast", tags=["forecast"])
KIT = "kitchen"


@router.get("")
def forecast(days: int = 7, method: str = "auto", location_id: str = "", k: Kitchen = Depends(allow("kitchen", "manage_business", module=KIT))):
    return k.cmd(gc.forecast.REQUESTS, gc.forecast.SERVICE, {"action": gc.forecast.ForecastAction.FORECAST.value, "days": days,
                                                             "method": method, "location_id": location_id})


@router.post("/targets")
def use_as_targets(body: dict, k: Kitchen = Depends(allow("manage_business", module=KIT))):
    """This week's target per product = its forecast (rounded up), for the products sent: {"items": {item_id: qty}}."""
    done = []
    for item_id, qty in (body.get("items") or {}).items():
        k.cmd(gc.planning.REQUESTS, gc.planning.SERVICE, {"action": "SET_TARGET", "item_id": item_id, "qty": math.ceil(float(qty))})
        done.append(item_id)
    return {"set": done}
