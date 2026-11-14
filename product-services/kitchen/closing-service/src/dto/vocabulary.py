# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names closing-service publishes."""
from enum import Enum


class Table(str, Enum):
    CLOSINGS = "closings"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    UNKNOWN_SALES_TYPE = "UNKNOWN_SALES_TYPE"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_DATE = "INVALID_DATE"
    STAFF_NAME_REQUIRED = "STAFF_NAME_REQUIRED"
    ALREADY_SUBMITTED = "ALREADY_SUBMITTED"
