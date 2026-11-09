# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions purchase-service accepts."""
from enum import Enum


class PurchaseAction(str, Enum):
    SAVE = "SAVE"
    COPY = "COPY"
    CANCEL = "CANCEL"
    RECEIVE = "RECEIVE"
