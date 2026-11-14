# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for warehouse-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import WarehouseAction
from . import cancel_pick, complete_pick, create_pick, move_lot, pick, recall, save_bin

TABLE = "warehouse_requests"
ROUTES = {
    WarehouseAction.SAVE_BIN: save_bin.handle,
    WarehouseAction.MOVE_LOT: move_lot.handle,
    WarehouseAction.CREATE_PICK: create_pick.handle,
    WarehouseAction.PICK: pick.handle,
    WarehouseAction.COMPLETE_PICK: complete_pick.handle,
    WarehouseAction.CANCEL_PICK: cancel_pick.handle,
    WarehouseAction.RECALL: recall.handle,
}
handle = ActionDispatcher(ROUTES, WarehouseAction, TABLE)
