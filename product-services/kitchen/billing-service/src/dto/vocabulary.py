# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names billing-service publishes."""
from enum import Enum


class Table(str, Enum):
    CUSTOMERS = "customers"
    INVOICES = "invoices"


class Kind(str, Enum):
    INVOICE = "invoice"
    CREDIT = "credit"


class InvoiceState(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    VOID = "void"


class Method(str, Enum):
    BANK = "bank"
    CASH = "cash"
    CARD = "card"
    PAYNOW = "paynow"
    CHEQUE = "cheque"
    OTHER = "other"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_BUSINESS = "UNKNOWN_BUSINESS"
    UNKNOWN_CUSTOMER = "UNKNOWN_CUSTOMER"
    UNKNOWN_INVOICE = "UNKNOWN_INVOICE"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"
    CUSTOMER_NAME_REQUIRED = "CUSTOMER_NAME_REQUIRED"
    INVALID_TERMS = "INVALID_TERMS"
    INVALID_EMAIL = "INVALID_EMAIL"
    NO_LINES = "NO_LINES"
    NOT_A_DRAFT = "NOT_A_DRAFT"
    NOT_OPEN = "NOT_OPEN"
    HAS_PAYMENTS = "HAS_PAYMENTS"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    MORE_THAN_DUE = "MORE_THAN_DUE"
    INVALID_METHOD = "INVALID_METHOD"
    INVALID_DATE = "INVALID_DATE"
    NO_EMAIL = "NO_EMAIL"
