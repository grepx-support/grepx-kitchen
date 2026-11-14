# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for closing-service vocabulary."""
from .closing_action import ClosingAction
from .vocabulary import ReasonCode, Table

__all__ = ["ClosingAction", "ReasonCode", "Table"]
