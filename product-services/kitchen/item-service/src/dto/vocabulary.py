# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names item-service publishes."""
from enum import Enum


class Table(str, Enum):
    ITEMS = "items"
    SUPPLIERS = "suppliers"
    RECIPES = "recipes"


class ItemKind(str, Enum):
    INGREDIENT = "ingredient"
    FINISHED = "finished"       # made by a kitchen (D6)
    SUPPLY = "supply"           # lids, straws, boxes


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    UNKNOWN_SUPPLIER = "UNKNOWN_SUPPLIER"
    INVALID_NAME = "INVALID_NAME"
    INVALID_KIND = "INVALID_KIND"
    INVALID_UNIT = "INVALID_UNIT"
    INVALID_COST = "INVALID_COST"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    NOT_FINISHED_GOOD = "NOT_FINISHED_GOOD"
    DUPLICATE_NAME = "DUPLICATE_NAME"
