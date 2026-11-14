/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Every widget the kitchen home can show. A new widget = a new file here plus one line below; nothing else changes.
import { WidgetRegistry } from "/assets/kit/index.js";
import closings from "./closings.js";
import cogs from "./cogs.js";
import deliveries from "./deliveries.js";
import hello from "./hello.js";
import kitchen from "./kitchen.js";
import money from "./money.js";
import moves from "./moves.js";
import needed from "./needed.js";
import orders from "./orders.js";
import safety from "./safety.js";

export const widgets = new WidgetRegistry();
[hello, cogs, money, kitchen, needed, safety, orders, deliveries, closings, moves].forEach((w) => widgets.register(w));
