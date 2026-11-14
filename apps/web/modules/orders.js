/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Orders: the board of purchase orders, the reorder recommendation, a new order, one order (ORD-01..10).
import { board } from "./orders/board.js";
import { detail } from "./orders/detail.js";
import { list } from "./orders/list.js";
import { newOrder } from "./orders/new-order.js";
import { recommend } from "./orders/recommend.js";

const ORDERS = { auth: "staff", tenant: true, area: "orders" };

export const routes = [
  { path: "/orders", feature: "orders", nav: "Orders", key: "p", icon: "cart", group: "Buying", perm: "orders", ...ORDERS, render: (el) => board(el) },
  { path: "/orders/list", feature: "orders", perm: ["orders", "warehouse_in"], ...ORDERS, render: (el, { args, ...q }) => list(el, q) },
  { path: "/orders/recommended", feature: "orders", perm: "orders", ...ORDERS, render: (el) => recommend(el) },
  { path: "/orders/new", feature: "orders", perm: "orders", ...ORDERS, render: (el) => newOrder(el) },
  { path: "/orders/:id", feature: "orders", ...ORDERS, render: (el, { args }) => detail(el, args[0]) },
];
