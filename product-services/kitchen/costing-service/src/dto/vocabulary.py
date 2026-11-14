# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names costing-service publishes."""
from enum import Enum


class Table(str, Enum):
    COST_DAYS = "cost_days"
    OVERHEADS = "overheads"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    INVALID_MONTH = "INVALID_MONTH"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_GROUP = "INVALID_GROUP"
    INVALID_SPLIT = "INVALID_SPLIT"
    NO_PLACES = "NO_PLACES"
