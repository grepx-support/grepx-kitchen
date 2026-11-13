/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the kitchen adds to the app-wide search (Ctrl K): its records and its quick actions. No pages of its own.
import { api } from "/assets/app.js";
import { has } from "./lib/business.js";

/** Each record kind: who may see it, how to load it (cached for a minute), how a row becomes a search result. */
const KINDS = [
  { perm: "view_stock", load: () => api("/stock/items").then((d) => d.items),
    show: (i) => ({ title: i.name, hint: `${i.category || i.kind} · ${i.unit}`, href: `#/stock?item=${i.id}`, icon: "box", area: "#0ea5e9", keywords: `${i.barcode || ""} ${i.category || ""}` }) },
  { perm: "orders", load: () => api("/orders/suppliers").then((d) => d.suppliers),
    show: (s) => ({ title: s.name, hint: "Supplier · new order", href: `#/orders/new?supplier=${s.id}`, icon: "cart", area: "#7c3aed" }) },
  { perm: "orders", load: () => api("/orders").then((d) => d.orders),
    show: (o) => ({ title: `${o.number} · ${o.supplier_name}`, hint: o.state, href: `#/orders/${o.id}`, icon: "clipboard", area: "#7c3aed", keywords: o.supplier_name }) },
];

class Cache {
  constructor(ttl = 60000) { Object.assign(this, { ttl, at: new Map() }); }
  get(kind) {
    const hit = this.at.get(kind);
    if (hit && Date.now() - hit.when < this.ttl) return hit.rows;
    const rows = kind.load().catch(() => []);
    this.at.set(kind, { when: Date.now(), rows });
    return rows;
  }
}

const cache = new Cache();

export const searchLabel = "Items, suppliers, orders";

export async function search(query) {
  const { rank } = await import("/assets/shell/finder/score.js");
  const lists = await Promise.all(KINDS.filter((k) => has(k.perm)).map(async (k) => (await cache.get(k)).map(k.show)));
  return rank(query, lists.flat());
}

export const actions = [
  { title: "Receive stock", icon: "inbox", href: "#/stock/in", perm: "warehouse_in", keywords: "goods in delivery supplier" },
  { title: "Send stock out", icon: "outbox", href: "#/stock/out", perm: "warehouse_out", keywords: "issue kitchen" },
  { title: "New purchase order", icon: "cart", href: "#/orders/new", perm: "orders", keywords: "buy supplier po" },
  { title: "Record waste", icon: "x", href: "#/stock/move", perm: "adjust_stock", keywords: "throw away spoiled expired" },
  { title: "Start a stock take", icon: "clipboard", href: "#/inventory/takes", perm: "adjust_stock", keywords: "count" },
  { title: "Plan a delivery run", icon: "truck", href: "#/runs", perm: "warehouse_out", keywords: "driver route" },
  { title: "Open kitchen terminal", icon: "monitor", href: "#/terminal", perm: "kitchen", keywords: "kds screen tablet production" },
  { title: "New invoice", icon: "receipt", href: "#/sales/new", perm: ["billing", "manage_business"], keywords: "bill customer sell" },
  { title: "Enter a supplier bill", icon: "inbox", href: "#/bills/new", perm: ["payables", "manage_business"], keywords: "supplier invoice payable" },
  { title: "3D warehouse", icon: "cube", href: "#/warehouse/3d", perm: "warehouse_in", keywords: "bins racks view" },
];

export const routes = [];
