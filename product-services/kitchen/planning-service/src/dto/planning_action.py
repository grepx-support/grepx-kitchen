# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions planning-service accepts."""
from enum import Enum


class PlanningAction(str, Enum):
    PRODUCTION_TARGET = "PRODUCTION_TARGET"
    SET_TARGET = "SET_TARGET"
    WAREHOUSE_OUT = "WAREHOUSE_OUT"
    WAREHOUSE_IN = "WAREHOUSE_IN"
    REORDER = "REORDER"
