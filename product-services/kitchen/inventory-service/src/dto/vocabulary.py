# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names inventory-service publishes."""
from enum import Enum


class InventoryAction(str, Enum):
    SET_PAR = "SET_PAR"            # minimum / maximum for an item at a location (0 = none)
    START_TAKE = "START_TAKE"      # a stock take: what the system expects, frozen now
    COUNT_TAKE = "COUNT_TAKE"      # counted quantities (any number of times)
    FINISH_TAKE = "FINISH_TAKE"    # variance -> stock corrected (stock-service ADJUST)
    CANCEL_TAKE = "CANCEL_TAKE"
    CHECK_ALERTS = "CHECK_ALERTS"  # low / negative / expiring / expired stock now (also every hour by the scheduler)
    ACK_ALERT = "ACK_ALERT"        # dealt with
    VALUATION = "VALUATION"        # what the stock is worth: at current cost and by lot cost
    ANALYSIS = "ANALYSIS"          # ABC by usage value, days of cover, waste by reason


class Table(str, Enum):
    PAR_LEVELS = "par_levels"
    STOCK_TAKES = "stock_takes"
    ALERTS = "alerts"


class AlertKind(str, Enum):
    LOW = "low"
    NEGATIVE = "negative"
    EXPIRING = "expiring"
    EXPIRED = "expired"


class TakeState(str, Enum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    UNKNOWN_TAKE = "UNKNOWN_TAKE"
    UNKNOWN_ALERT = "UNKNOWN_ALERT"
    TAKE_CLOSED = "TAKE_CLOSED"
    TAKE_OPEN_HERE = "TAKE_OPEN_HERE"
    NOTHING_COUNTED = "NOTHING_COUNTED"
    INVALID_LEVEL = "INVALID_LEVEL"
    INVALID_QUANTITY = "INVALID_QUANTITY"
