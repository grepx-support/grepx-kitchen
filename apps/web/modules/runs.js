/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Delivery runs: the dispatch board, one run (order, start), and the driver's phone view with proof of delivery.
import { board } from "./runs/board.js";
import { driver } from "./runs/driver.js";
import { runPage } from "./runs/run.js";

const RUNS = { auth: "staff", tenant: true };

export const routes = [
  { path: "/runs", nav: "Delivery runs", key: "r", icon: "truck", area: "runs", group: "Warehouse", perm: "warehouse_out", ...RUNS, render: board },
  { path: "/runs/:id", area: "runs", perm: "warehouse_out", ...RUNS, render: (el, { args }) => runPage(el, args[0]) },
  { path: "/driver", nav: "My deliveries", icon: "truck", area: "driver", group: "Daily", perm: "delivery", ...RUNS, render: driver },
];
