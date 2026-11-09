# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions business-service accepts."""
from enum import Enum


class BusinessAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SAVE_LOCATION = "SAVE_LOCATION"
