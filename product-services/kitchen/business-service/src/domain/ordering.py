# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The order a business lists its rows in (set by dragging them in setup)."""
from __future__ import annotations

INVALID_LIST = "INVALID_LIST"


def positions(ids, known: set[str]) -> dict[str, int]:
    """id -> position (0, 1, ...). ids must be distinct rows of this business; rows not named keep their place after them."""
    if not isinstance(ids, list) or not ids or len(ids) > 2000:
        raise ValueError(INVALID_LIST)
    ids = [str(i) for i in ids]
    if len(set(ids)) != len(ids) or not set(ids) <= known:
        raise ValueError(INVALID_LIST)
    return {key: n for n, key in enumerate(ids)}
