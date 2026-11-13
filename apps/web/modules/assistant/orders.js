/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Assistant skills about buying: what is on order (or one order by its number) and what to order now.
import { fit } from "/assets/shell/assistant/intent.js";
import { business, find } from "./util.js";

const STAGE = { on_order: "on order", received: "received", billed: "billed", paid: "paid", cancelled: "cancelled" };

export const onOrder = {
  id: "on-order", title: "What is on order", perm: ["orders", "warehouse_in"],
  words: ["order", "orders", "coming", "way", "arriving", "arrive", "purchase", "po", "delivery", "expected"],
  examples: ["what is on order", "which orders are arriving"],
  test: (t) => (/\bpo-?\s?\d+/i.test(t) ? 0.97 : /\b(on order|arriving|coming|on (the|its) way|expected|ordered)\b/i.test(t) ? 0.9 : fit(t, onOrder) * 0.7),
  answer: async (t, ctx) => {
    const all = (await ctx.api("/orders")).orders || [];
    const asked = t.match(/po-?\s?(\d+)/i);
    if (asked) {
      const o = all.find((x) => Number(x.number.replace(/\D/g, "")) === Number(asked[1]));
      if (!o) return { text: `I can't find PO-${asked[1].padStart(4, "0")}.`, fresh: false };
      return { text: `${o.number} from ${o.supplier_name} is ${STAGE[o.stage] || o.stage}.`, kpis: [{ label: "Lines", value: o.lines.length }, { label: "Stage", value: STAGE[o.stage] }],
        items: o.lines.map((l) => ({ title: l.item_name, value: `${ctx.num(l.qty)} ${l.unit}` })), links: [{ label: `Open ${o.number}`, href: `#/orders/${o.id}` }] };
    }
    const open = all.filter((o) => o.stage === "on_order");
    return { text: open.length ? `${open.length} order${open.length === 1 ? " is" : "s are"} on the way:` : "Nothing is on order right now.",
      items: open.map((o) => ({ title: `${o.number} · ${o.supplier_name}`, sub: o.lines.map((l) => l.item_name).join(", "), value: `${o.lines.length} lines`, href: `#/orders/${o.id}` })),
      chips: ["what should I order", "which bills do we need to pay"] };
  },
};

export const toOrder = {
  id: "to-order", title: "What to order", perm: ["orders"],
  words: ["order", "buy", "reorder", "purchase", "need", "should", "shopping", "replenish"],
  examples: ["what should I order", "what do we need to buy"],
  test: (t) => (/\b(should|need to|must|to) (order|buy|reorder)\b|\breorder\b|\bshopping\b/i.test(t) ? 0.9 : fit(t, toOrder) * 0.7),
  answer: async (t, ctx) => {
    const holding = (await business()).locations.find((l) => l.holding);
    if (!holding) return { text: "No place holds stock yet - set one in Setup → Locations." };
    const rec = await ctx.api(`/orders/recommendation?location_id=${holding.id}`);
    const lines = (rec.lines || []).filter((l) => l.recommended > 0);
    const item = find(t, lines);
    const shown = item ? [item] : lines;
    return { text: shown.length ? `From usage, ${holding.name} should order:` : "Stock covers the coming week - nothing to order.",
      items: shown.map((l) => ({ title: l.name, sub: l.supplier_name || "no supplier", value: `${ctx.num(l.recommended)} ${l.unit}`, href: "#/orders/recommended" })),
      links: [{ label: "Make the orders", href: "#/orders/recommended" }] };
  },
};

export const ORDERS = [onOrder, toOrder];
