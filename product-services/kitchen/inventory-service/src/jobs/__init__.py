# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reactions: the scheduler's tick checks every business for alerts."""
from .tick import handle_tick

__all__ = ["handle_tick"]
