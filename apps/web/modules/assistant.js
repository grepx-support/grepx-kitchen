/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the assistant knows about the kitchen: its skills (stock, money, orders, kitchen). No pages of its own.
import { KITCHEN } from "./assistant/kitchen.js";
import { MONEY } from "./assistant/money.js";
import { ORDERS } from "./assistant/orders.js";
import { STOCK } from "./assistant/stock.js";

export const skills = [...STOCK, ...ORDERS, ...MONEY, ...KITCHEN];
export const routes = [];
