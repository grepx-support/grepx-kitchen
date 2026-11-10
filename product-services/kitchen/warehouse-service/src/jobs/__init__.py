# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reactions: an accepted stock change moves the lots it touched."""
from .follow import follow_stock

__all__ = ["follow_stock"]
