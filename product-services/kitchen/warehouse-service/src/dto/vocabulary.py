# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names warehouse-service publishes."""
from enum import Enum


class WarehouseAction(str, Enum):
    SAVE_BIN = "SAVE_BIN"            # a shelf / bin / fridge in a location, in a zone
    MOVE_LOT = "MOVE_LOT"            # putaway: put a lot in a bin
    CREATE_PICK = "CREATE_PICK"      # a pick list for a warehouse-out, lots chosen first-expiry-first-out
    PICK = "PICK"                    # how much of a line was picked
    COMPLETE_PICK = "COMPLETE_PICK"  # picked -> warehouse-out (stock-service SEND)
    CANCEL_PICK = "CANCEL_PICK"


class Table(str, Enum):
    BINS = "bins"
    LOTS = "lots"
    PICKS = "picks"
    FOLLOWED = "followed"


class PickState(str, Enum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"


class Zone(str, Enum):
    DRY = "dry"
    CHILLED = "chilled"
    FROZEN = "frozen"
    PACKAGING = "packaging"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    UNKNOWN_BIN = "UNKNOWN_BIN"
    UNKNOWN_LOT = "UNKNOWN_LOT"
    UNKNOWN_PICK = "UNKNOWN_PICK"
    INVALID_CODE = "INVALID_CODE"
    INVALID_ZONE = "INVALID_ZONE"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    NO_LINES = "NO_LINES"
    NOTHING_PICKED = "NOTHING_PICKED"
    PICK_CLOSED = "PICK_CLOSED"
    SAME_LOCATION = "SAME_LOCATION"
