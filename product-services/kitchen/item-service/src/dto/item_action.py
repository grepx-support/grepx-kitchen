# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions item-service accepts."""
from enum import Enum


class ItemAction(str, Enum):
    SAVE_ITEM = "SAVE_ITEM"
    SAVE_SUPPLIER = "SAVE_SUPPLIER"
    SAVE_RECIPE = "SAVE_RECIPE"
    SAVE_RECIPE_CARD = "SAVE_RECIPE_CARD"   # the chef's card: method, station, times, yield, plating
    SET_COSTS = "SET_COSTS"      # new costs for several items ({item_id: cost}), kept in each item's cost history
    REORDER = "REORDER"          # the order items or suppliers are listed in (drag and drop in setup)
