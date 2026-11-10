# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names stock-service publishes."""
from enum import Enum


class Table(str, Enum):
    STOCK_LEVELS = "stock_levels"
    STOCK_MOVEMENTS = "stock_movements"
    DELIVERIES = "deliveries"        # one per warehouse-out: sent -> delivered


class MovementKind(str, Enum):
    RECEIVE = "receive"              # into a location from a supplier or anywhere outside the business
    SEND_OUT = "send_out"            # warehouse out: leaves the holding place ...
    SEND_IN = "send_in"              # ... and arrives at the location
    TRANSFER_OUT = "transfer_out"    # store to store (R2)
    TRANSFER_IN = "transfer_in"
    PRODUCE = "produce"              # finished goods made by a kitchen (KIT-08)
    USE = "use"                      # ingredients used by a kitchen (KIT-09)
    ADJUST = "adjust"                # correction with a reason (R3)
    COUNT = "count"                  # counted at closing: replaces system stock, difference kept (Q6)


class DeliveryState(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    NO_LINES = "NO_LINES"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    SAME_LOCATION = "SAME_LOCATION"
    NOT_HOLDING_LOCATION = "NOT_HOLDING_LOCATION"
    NOT_A_KITCHEN = "NOT_A_KITCHEN"
    NOT_FINISHED_GOOD = "NOT_FINISHED_GOOD"
    REASON_REQUIRED = "REASON_REQUIRED"
    UNKNOWN_DELIVERY = "UNKNOWN_DELIVERY"
    ALREADY_DELIVERED = "ALREADY_DELIVERED"
