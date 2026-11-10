# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions item-service accepts."""
from enum import Enum


class ItemAction(str, Enum):
    SAVE_ITEM = "SAVE_ITEM"
    SAVE_SUPPLIER = "SAVE_SUPPLIER"
    SAVE_RECIPE = "SAVE_RECIPE"
    REORDER = "REORDER"          # the order items or suppliers are listed in (drag and drop in setup)
