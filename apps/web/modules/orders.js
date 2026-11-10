/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Orders: the board of purchase orders, the reorder recommendation, a new order, one order (ORD-01..10).
import { board } from "./orders/board.js";
import { detail } from "./orders/detail.js";
import { newOrder } from "./orders/new-order.js";
import { recommend } from "./orders/recommend.js";

const ORDERS = { auth: "staff", tenant: true, area: "orders" };

export const routes = [
  { path: "/orders", nav: "Orders", icon: "cart", group: "Buying", perm: "orders", ...ORDERS, render: (el) => board(el) },
  { path: "/orders/recommended", perm: "orders", ...ORDERS, render: (el) => recommend(el) },
  { path: "/orders/new", perm: "orders", ...ORDERS, render: (el) => newOrder(el) },
  { path: "/orders/:id", ...ORDERS, render: (el, { args }) => detail(el, args[0]) },
];
