# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions billing-service accepts."""
from enum import Enum


class BillingAction(str, Enum):
    SAVE_CUSTOMER = "SAVE_CUSTOMER"
    SAVE_INVOICE = "SAVE_INVOICE"
    ISSUE_INVOICE = "ISSUE_INVOICE"
    RECORD_PAYMENT = "RECORD_PAYMENT"
    VOID_INVOICE = "VOID_INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    SUMMARY = "SUMMARY"
    MONTHLY = "MONTHLY"
    MARGINS = "MARGINS"
    STATEMENT = "STATEMENT"
    SEND_REMINDER = "SEND_REMINDER"
