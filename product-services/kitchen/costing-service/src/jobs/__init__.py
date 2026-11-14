# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reactions: a closing's count was applied to stock -> cost of that period."""
from .count import handle_count

__all__ = ["handle_count"]
