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
    DELIVERED = "DELIVERED"      # the destination confirms a warehouse-out delivery arrived
    WASTE = "WASTE"              # thrown away with a reason (expired, spoiled, damaged, overproduced, other)
    RETURN = "RETURN"            # goods sent back to the supplier (credited on their bill)
    BREAK_DOWN = "BREAK_DOWN"    # bulk into its parts (a whole chicken into cuts) at one location
    SELL = "SELL"                # goods on an issued customer invoice leave the location they are sent from
