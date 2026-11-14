# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions payables-service accepts."""
from enum import Enum


class PayablesAction(str, Enum):
    SAVE_BILL = "SAVE_BILL"
    APPROVE_BILL = "APPROVE_BILL"
    RECORD_PAYMENT = "RECORD_PAYMENT"
    VOID_BILL = "VOID_BILL"
    SUMMARY = "SUMMARY"
    MONTHLY = "MONTHLY"
    PRICES = "PRICES"                  # price history per supplier and item, and the recent rises (jumps first)
