# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for item-service."""
from grepx_service import ActionDispatcher

from dto import ItemAction
from . import save_item, save_recipe, save_supplier

TABLE = "item_requests"
ROUTES = {
    ItemAction.SAVE_ITEM: save_item.handle,
    ItemAction.SAVE_SUPPLIER: save_supplier.handle,
    ItemAction.SAVE_RECIPE: save_recipe.handle,
}
handle = ActionDispatcher(ROUTES, ItemAction, TABLE)
