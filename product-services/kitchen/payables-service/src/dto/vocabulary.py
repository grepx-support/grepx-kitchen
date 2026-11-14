# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names payables-service publishes."""
from enum import Enum


class Table(str, Enum):
    BILLS = "bills"


class BillState(str, Enum):
    ENTERED = "entered"          # typed in, waiting for approval
    APPROVED = "approved"        # ok to pay
    PAID = "paid"
    VOID = "void"


class Match(str, Enum):
    MATCHED = "matched"          # billed = received, at the expected price (within tolerance)
    CHECK = "check"              # something differs: see issues
    NO_ORDER = "no_order"        # a bill without a purchase order (services, utilities ...)


class Issue(str, Enum):
    NOT_ORDERED = "not_ordered"
    MORE_THAN_RECEIVED = "more_than_received"
    NOT_RECEIVED_YET = "not_received_yet"
    PRICE_DIFFERS = "price_differs"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_SUPPLIER = "UNKNOWN_SUPPLIER"
    UNKNOWN_ORDER = "UNKNOWN_ORDER"
    UNKNOWN_BILL = "UNKNOWN_BILL"
    ORDER_OF_ANOTHER_SUPPLIER = "ORDER_OF_ANOTHER_SUPPLIER"
    SUPPLIER_REF_REQUIRED = "SUPPLIER_REF_REQUIRED"
    DUPLICATE_BILL = "DUPLICATE_BILL"
    INVALID_DATE = "INVALID_DATE"
    NOT_ENTERED = "NOT_ENTERED"
    NOT_APPROVED = "NOT_APPROVED"
    NOTE_REQUIRED = "NOTE_REQUIRED"
    HAS_PAYMENTS = "HAS_PAYMENTS"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    MORE_THAN_DUE = "MORE_THAN_DUE"
    INVALID_METHOD = "INVALID_METHOD"
    INVALID_LANDED_COST = "INVALID_LANDED_COST"
    INVALID_SPREAD = "INVALID_SPREAD"
    NOT_RETURNABLE = "NOT_RETURNABLE"
    INVALID_REASON = "INVALID_REASON"
    NO_LINES = "NO_LINES"
    MORE_THAN_BILLED = "MORE_THAN_BILLED"
    INVALID_QUANTITY = "INVALID_QUANTITY"
