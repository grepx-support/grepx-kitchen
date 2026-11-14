# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions costing-service accepts."""
from enum import Enum


class CostingAction(str, Enum):
    SET_OVERHEAD = "SET_OVERHEAD"
    SUMMARY = "SUMMARY"
    SHARE_OVERHEAD = "SHARE_OVERHEAD"    # a cost paid once for several places, split equally / by sales / by weights
    COPY_OVERHEADS = "COPY_OVERHEADS"    # start a month from the month before
    OVERHEADS = "OVERHEADS"              # the monthly costs page: lines, totals, changes, categories
