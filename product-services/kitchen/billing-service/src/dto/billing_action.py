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
    SAVE_QUOTE = "SAVE_QUOTE"          # a catering / event quotation: customer, event, menu lines, valid for N days
    SEND_QUOTE = "SEND_QUOTE"          # number it (Q-2026-0001) and send it to the customer, the PDF attached
    ACCEPT_QUOTE = "ACCEPT_QUOTE"      # the customer said yes: it becomes an order (SO-2026-0001)
    DECLINE_QUOTE = "DECLINE_QUOTE"    # the customer said no (reason kept)
    CANCEL_QUOTE = "CANCEL_QUOTE"      # withdrawn by the business (a quote or an order not yet invoiced)
    INVOICE_ORDER = "INVOICE_ORDER"    # the order becomes a draft invoice with the same lines
    QUOTES = "QUOTES"                  # quotes and orders as a reader sees them (expired...), the pipeline and win rate
