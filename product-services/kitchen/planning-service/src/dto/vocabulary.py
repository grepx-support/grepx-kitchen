# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names planning-service publishes."""
from enum import Enum


class Table(str, Enum):
    PLANS = "plans"


class PlanKind(str, Enum):
    TARGET = "target"              # manual production targets / event extras for one week
    REORDER = "reorder"            # a reorder recommendation, kept so the next one can be compared (ORD-04)


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    NOT_A_KITCHEN = "NOT_A_KITCHEN"
    NOT_HOLDING_LOCATION = "NOT_HOLDING_LOCATION"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    INVALID_DATE = "INVALID_DATE"
