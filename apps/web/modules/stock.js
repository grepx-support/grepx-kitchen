/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Stock: levels and history, warehouse out with suggestions, warehouse in, transfer and adjust, the delivery board (INV-01..11).
import { deliveries } from "./stock/deliveries.js";
import { warehouseIn } from "./stock/in.js";
import { levels } from "./stock/levels.js";
import { move } from "./stock/move.js";
import { warehouseOut } from "./stock/out.js";

const STOCK = { auth: "staff", tenant: true, group: "Stock" };

export const routes = [
  { path: "/stock", nav: "Stock levels", key: "s", icon: "box", area: "stock", perm: "view_stock", ...STOCK, render: levels },
  { path: "/stock/out", nav: "Warehouse out", key: "o", icon: "outbox", area: "out", perm: "warehouse_out", ...STOCK, render: warehouseOut },
  { path: "/stock/in", nav: "Warehouse in", key: "i", icon: "inbox", area: "in", perm: "warehouse_in", ...STOCK, render: warehouseIn },
  { path: "/stock/move", nav: "Transfer", key: "t", icon: "swap", area: "move", perm: "transfer", ...STOCK, render: move },
  { path: "/stock/deliveries", nav: "Deliveries", key: "d", icon: "truck", area: "deliveries", perm: "delivery", ...STOCK, render: deliveries },
];
