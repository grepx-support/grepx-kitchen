/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Assistant skills about stock: what is low or below zero, what is expiring or expired, and how much of an item is where.
import { fit } from "/assets/shell/assistant/intent.js";
import { find } from "./util.js";

const alertsOf = (ctx) => ctx.api("/inventory/alerts").then((d) => d.alerts || []);

export const low = {
  id: "low", title: "Low or missing stock", perm: ["view_stock", "manage_business"],
  words: ["low", "short", "shortage", "below", "minimum", "min", "out", "negative", "zero", "alert", "running"],
  examples: ["what is low on stock", "what is running out", "anything below zero"],
  answer: async (t, ctx) => {
    const rows = (await alertsOf(ctx)).filter((a) => ["low", "negative", "out"].includes(a.kind));
    if (!rows.length) return { text: "Nothing is low or below zero right now. 👍", chips: ["what is expiring soon", "what should I order"] };
    return { text: `${rows.length} thing${rows.length === 1 ? " needs" : "s need"} attention:`, kpis: [{ label: "Below zero", value: rows.filter((a) => a.kind === "negative").length, tone: "bad", href: "#/inventory" },
      { label: "Below minimum", value: rows.filter((a) => a.kind === "low").length, tone: "warn", href: "#/inventory" }],
      items: rows.map((a) => ({ title: a.item_name, sub: `${a.location_name} · ${{ negative: "below zero - count it again", out: "out of stock" }[a.kind] || "below minimum"}`,
        value: `${ctx.num(a.qty)} ${a.unit || ""}`, tone: a.kind === "low" ? "warn" : "bad", href: `#/stock?item=${a.item_id}` })),
      chips: ["what should I order", "what is expiring soon"] };
  },
};

export const expiring = {
  id: "expiring", title: "Expired or expiring", perm: ["view_stock", "manage_business"],
  words: ["expire", "expiring", "expired", "expiry", "spoil", "spoiled", "old", "date", "fresh", "waste"],
  examples: ["what is expiring soon", "what has expired"],
  answer: async (t, ctx) => {
    const rows = (await alertsOf(ctx)).filter((a) => a.kind === "expired" || a.kind === "expiring").sort((a, z) => a.days_left - z.days_left);
    if (!rows.length) return { text: "Nothing has expired and nothing expires in the next two days." };
    const gone = rows.filter((a) => a.kind === "expired").length;
    return { text: gone ? `${gone} lot${gone === 1 ? " has" : "s have"} expired - use first or record as waste:` : "These expire in the next two days - use them first:",
      kpis: [{ label: "Expired", value: gone, tone: "bad", href: "#/warehouse" }, { label: "Expiring", value: rows.length - gone, tone: "warn", href: "#/warehouse" }],
      items: rows.map((a) => ({ title: a.item_name, sub: `${a.location_name} · ${a.days_left < 0 ? `${-a.days_left} day(s) ago` : a.days_left === 0 ? "today" : `in ${a.days_left} day(s)`}`,
        value: `${ctx.num(a.qty)} ${a.unit || ""}`, tone: a.days_left < 0 ? "bad" : "warn", href: "#/warehouse" })),
      links: [{ label: "Warehouse floor (3D)", href: "#/warehouse/3d" }] };
  },
};

export const howMuch = {
  id: "how-much", title: "How much of an item", perm: ["view_stock", "manage_business"],
  words: ["much", "many", "left", "have", "level", "quantity", "qty", "hold", "stock", "where"],
  examples: ["how much paneer do we have", "where is the basmati rice"],
  test: (t, ctx) => (/how (much|many)|do we have|where is|left of|stock of/i.test(t) ? 0.85 : fit(t, howMuch) * 0.5),
  answer: async (t, ctx) => {
    const levels = (await ctx.api("/stock")).levels || [];
    const item = find(t, levels.map((l) => ({ id: l.item_id, name: l.item_name })));
    if (!item) return { text: "Which item? Try \"how much paneer do we have\".", fresh: false };
    const here = levels.filter((l) => l.item_id === item.id), total = here.reduce((n, l) => n + l.qty, 0), unit = here[0]?.unit || "";
    return { text: `${item.name}: ${ctx.num(total)} ${unit} in all.`, kpis: [{ label: "In all", value: `${ctx.num(total)} ${unit}`, tone: total < 0 ? "bad" : "", href: `#/stock?item=${item.id}` },
      { label: "Places", value: here.length }],
      items: here.sort((a, z) => z.qty - a.qty).map((l) => ({ title: l.location_name, value: `${ctx.num(l.qty)} ${unit}`, tone: l.qty < 0 ? "bad" : "", href: `#/stock?item=${item.id}` })),
      chips: [`forecast for ${item.name.toLowerCase()}`, "what is low on stock"] };
  },
};

export const STOCK = [low, expiring, howMuch];
