# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names delivery-service publishes."""
from enum import Enum


class DeliveryAction(str, Enum):
    PLAN_RUN = "PLAN_RUN"      # a driver, a day, warehouse-out trips in order
    SET_STOPS = "SET_STOPS"    # add, remove or reorder the stops not yet visited
    START_RUN = "START_RUN"    # the van leaves: arrival times from now
    ARRIVE = "ARRIVE"          # at a stop
    DELIVER = "DELIVER"        # handed over: receiver, signature -> the trip is delivered in stock
    FAIL_STOP = "FAIL_STOP"    # could not deliver (closed, refused...): the trip can go on another run
    CANCEL_RUN = "CANCEL_RUN"  # a run that has not left


class Table(str, Enum):
    RUNS = "runs"


class RunState(str, Enum):
    PLANNED = "planned"
    ON_ROAD = "on_road"
    DONE = "done"
    CANCELLED = "cancelled"


class StopState(str, Enum):
    PENDING = "pending"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    FAILED = "failed"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_RUN = "UNKNOWN_RUN"
    UNKNOWN_STOP = "UNKNOWN_STOP"
    UNKNOWN_DELIVERY = "UNKNOWN_DELIVERY"
    ALREADY_DELIVERED = "ALREADY_DELIVERED"
    ON_ANOTHER_RUN = "ON_ANOTHER_RUN"
    NO_STOPS = "NO_STOPS"
    INVALID_DATE = "INVALID_DATE"
    INVALID_TIME = "INVALID_TIME"
    INVALID_NAME = "INVALID_NAME"
    WRONG_STATE = "WRONG_STATE"
    RECEIVER_REQUIRED = "RECEIVER_REQUIRED"
    SIGNATURE_TOO_LARGE = "SIGNATURE_TOO_LARGE"
    REASON_REQUIRED = "REASON_REQUIRED"
