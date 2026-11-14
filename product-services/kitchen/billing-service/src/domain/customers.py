# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A customer as kept: name, contacts, billing address, tax number, payment terms (days), their prices (discount %,
fixed prices per item)."""
import re

from dto import ReasonCode

from .pricing import clean_pricing

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_customer(body: dict) -> dict:
    name = str(body.get("name") or "").strip()[:120]
    if not name:
        raise ValueError(ReasonCode.CUSTOMER_NAME_REQUIRED)
    email = str(body.get("email") or "").strip().lower()[:120]
    if email and not EMAIL.match(email):
        raise ValueError(ReasonCode.INVALID_EMAIL)
    try:
        terms = int(body.get("terms_days") if body.get("terms_days") not in (None, "") else 30)
    except (TypeError, ValueError):
        raise ValueError(ReasonCode.INVALID_TERMS)
    if not 0 <= terms <= 365:
        raise ValueError(ReasonCode.INVALID_TERMS)
    text = lambda k, n=200: str(body.get(k) or "").strip()[:n]   # noqa: E731
    return {"name": name, "email": email, "phone": text("phone", 30), "address": text("address", 400), "tax_number": text("tax_number", 40),
            "contact": text("contact", 80), "terms_days": terms, "active": body.get("active") is not False,
            "pricing": clean_pricing(body.get("pricing"))}
