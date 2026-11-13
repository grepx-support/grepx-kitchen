/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Each area of the kitchen app has a colour (product.json "areas") and an icon - used by the menu, headers and tiles.
import { state } from "/assets/app.js";

const ICONS = { home: "home", kitchen: "pot", stock: "box", out: "outbox", in: "inbox", move: "swap", deliveries: "truck",
  orders: "cart", closing: "clipboard", costs: "chart", setup: "settings", platform: "building",
  floor: "layout", runs: "truck", driver: "map", inventory: "alert", outbox: "send", money: "receipt", terminal: "monitor" };

export const area = (name) => state.product?.areas?.[name] || "var(--primary)";
export const areaIcon = (name) => ICONS[name] || "dot";

/** Page header props for an area: pageHead({...head("stock"), title, subtitle}) */
export const head = (name) => ({ area: area(name), icon: areaIcon(name) });
