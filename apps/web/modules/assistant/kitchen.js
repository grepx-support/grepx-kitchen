/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Assistant skills about the kitchen: the sales forecast (for one product or all), what to cook this week, deliveries today.
import { isKitchen, remembered } from "../lib/place.js";
import { business, find } from "./util.js";

export const forecast = {
  id: "forecast", title: "Sales forecast", perm: ["kitchen", "manage_business"],
  words: ["forecast", "predict", "prediction", "tomorrow", "expect", "sell", "demand", "next", "week", "will"],
  examples: ["what will we sell tomorrow", "forecast for biryani"],
  answer: async (t, ctx) => {
    const d = await ctx.api("/forecast?days=7", 120);
    const product = find(t, d.products);
    if (product) {
      const rows = d.rows.filter((r) => r.item_id === product.item_id);
      return { text: `${product.name}: about ${ctx.num(product.first_day)} ${product.unit} tomorrow, ${ctx.num(product.total)} in the next 7 days.`,
        kpis: [{ label: "Tomorrow", value: ctx.num(product.first_day) }, { label: "7 days", value: ctx.num(product.total) }],
        items: rows.map((r) => ({ title: r.location_name, sub: `${r.error == null ? "not tested yet" : `usually ${r.error}% off`}`, value: `${ctx.num(r.forecast[0]?.qty)} tomorrow` })),
        links: [{ label: "Forecast page", href: "#/kitchen/forecast" }] };
    }
    return { text: "Tomorrow, across every place:", items: d.products.map((p) => ({ title: p.name, sub: `${ctx.num(p.total)} ${p.unit} in 7 days`, value: `${ctx.num(p.first_day)} ${p.unit}`, href: "#/kitchen/forecast" })),
      chips: d.products.slice(0, 2).map((p) => `forecast for ${p.name.toLowerCase()}`) };
  },
};

export const cook = {
  id: "cook", title: "What to cook", perm: ["kitchen", "manage_business"],
  words: ["make", "cook", "produce", "batch", "batches", "target", "prep", "production", "kitchen"],
  examples: ["what should the kitchen make this week", "how many batches today"],
  answer: async (t, ctx) => {
    const b = await business(), place = remembered(b.locations, isKitchen);
    if (!place) return { text: "There is no kitchen set up yet." };
    const tg = await ctx.api(`/kitchen/target?location_id=${place}`);
    return { text: `This week's targets (week of ${tg.week}):`, items: tg.lines.map((l) => ({ title: l.name, sub: `on hand ${ctx.num(l.on_hand)} · ${l.batches ?? "-"} batch(es)`,
      value: l.target == null ? "no target" : `${ctx.num(l.target)} ${l.unit}`, href: "#/kitchen" })), links: [{ label: "Kitchen screen", href: "#/kitchen" }, { label: "Use the forecast as targets", href: "#/kitchen/forecast" }] };
  },
};

export const deliveries = {
  id: "deliveries", title: "Deliveries today", perm: ["warehouse_out", "manage_business", "deliver"],
  words: ["delivery", "deliveries", "van", "driver", "road", "sent", "truck", "dispatch", "trip"],
  examples: ["what deliveries are on the road today"],
  answer: async (t, ctx) => {
    const today = new Date().toISOString().slice(0, 10);
    const rows = ((await ctx.api("/stock/deliveries")).deliveries || []).filter((x) => x.date === today);
    const road = rows.filter((x) => x.state !== "delivered");
    return { text: rows.length ? `${rows.length} trip(s) today, ${road.length} still on the road.` : "No deliveries today.",
      items: rows.map((x) => ({ title: `${x.from} → ${x.to}`, sub: x.by, value: x.state, tone: x.state === "delivered" ? "good" : "warn", href: "#/stock/deliveries" })),
      links: [{ label: "Delivery runs", href: "#/runs" }] };
  },
};

export const KITCHEN = [forecast, cook, deliveries];
