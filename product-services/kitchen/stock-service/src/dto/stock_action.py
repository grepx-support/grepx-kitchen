# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions stock-service accepts."""
from enum import Enum


class StockAction(str, Enum):
    RECEIVE = "RECEIVE"
    SEND = "SEND"
    TRANSFER = "TRANSFER"
    PRODUCE = "PRODUCE"
    USE = "USE"
    ADJUST = "ADJUST"
    COUNT = "COUNT"
