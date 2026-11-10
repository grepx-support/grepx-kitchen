# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names purchase-service publishes."""
from enum import Enum


class Table(str, Enum):
    PURCHASE_ORDERS = "purchase_orders"


class PoState(str, Enum):
    SAVED = "saved"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_ORDER = "UNKNOWN_ORDER"
    UNKNOWN_SUPPLIER = "UNKNOWN_SUPPLIER"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    NOT_HOLDING_LOCATION = "NOT_HOLDING_LOCATION"
    NO_LINES = "NO_LINES"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    ALREADY_CLOSED = "ALREADY_CLOSED"
    NO_CONTACT = "NO_CONTACT"
    INVALID_CHANNEL = "INVALID_CHANNEL"
