# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions closing-service accepts."""
from enum import Enum


class ClosingAction(str, Enum):
    SUBMIT = "SUBMIT"
