# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names business-service publishes: its tables, location kinds, modules, reason codes."""
from enum import Enum


class Table(str, Enum):
    BUSINESSES = "businesses"
    LOCATIONS = "locations"


class LocationKind(str, Enum):
    KITCHEN = "kitchen"
    WAREHOUSE = "warehouse"
    STORE = "store"
    TRUCK = "truck"


class Module(str, Enum):
    KITCHEN = "kitchen"
    INVENTORY = "inventory"
    ORDERS = "orders"
    COSTING = "costing"
    CLOSING = "closing"
    WAREHOUSE = "warehouse"            # lots, bins, picking, scanning
    DELIVERY = "delivery"              # delivery runs and the driver's screen
    SALES = "sales"                    # customers and invoices
    QUOTES = "quotes"                  # catering quotations -> orders
    PURCHASING = "purchasing"          # supplier bills and paying them
    TEAM = "team"                      # people and their documents
    ROSTER = "roster"                  # shifts and clocking in
    LEAVE = "leave"
    PAYROLL = "payroll"
    FUNDS = "funds"
    FOOD_SAFETY = "food_safety"
    CHEF = "chef"                      # recipe cards, allergens, stations
    FORECAST = "forecast"
    IMPORT_EXPORT = "import_export"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    BUSINESS_EXISTS = "BUSINESS_EXISTS"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    INVALID_NAME = "INVALID_NAME"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    INVALID_TIMEZONE = "INVALID_TIMEZONE"
    INVALID_KIND = "INVALID_KIND"
    INVALID_SETTING = "INVALID_SETTING"
    NO_HOLDING_LOCATION = "NO_HOLDING_LOCATION"
    INVALID_LIST = "INVALID_LIST"
