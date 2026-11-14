# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names business-service publishes: its tables, location kinds, modules, reason codes."""
from enum import Enum


class Table(str, Enum):
    BUSINESSES = "businesses"
    LOCATIONS = "locations"


class LocationKind(str, Enum):
    KITCHEN = "kitchen"
    WAREHOUSE = "warehouse"
    STORE = "store"
    TRUCK = "truck"


class Module(str, Enum):
    KITCHEN = "kitchen"
    INVENTORY = "inventory"
    ORDERS = "orders"
    COSTING = "costing"
    CLOSING = "closing"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    BUSINESS_EXISTS = "BUSINESS_EXISTS"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    INVALID_NAME = "INVALID_NAME"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    INVALID_TIMEZONE = "INVALID_TIMEZONE"
    INVALID_KIND = "INVALID_KIND"
    INVALID_SETTING = "INVALID_SETTING"
    NO_HOLDING_LOCATION = "NO_HOLDING_LOCATION"
    INVALID_LIST = "INVALID_LIST"
