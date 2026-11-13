/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The 3D cost landscape laid out - plain maths, no drawing. Days run left to right, places front to back; each count
// period is a column as tall as its sales, split into where that money went: ingredients, labour, rent, other and,
// on top, what was left (profit). When costs beat sales the column stands taller than its sales, with a red line at sales.
export const PARTS = [
  { key: "ingredient_cost", label: "Ingredients", colour: 0xf97316 },
  { key: "labour", label: "Labour", colour: 0x8b5cf6 },
  { key: "rent", label: "Rent", colour: 0x0ea5e9 },
  { key: "other", label: "Other", colour: 0x94a3b8 },
  { key: "profit", label: "Profit", colour: 0x22c55e },
];
const HEIGHT = 7, STEP_X = 1.25, STEP_Z = 2.8;

const costOf = (d) => ["ingredient_cost", "labour", "rent", "other"].reduce((n, k) => n + (Number(d[k]) || 0), 0);

/** In range -> green, above -> red, below -> blue (a COGS that low usually means a count or a price is off). */
export function cogsTone(pct, [lo, hi] = [25, 35]) {
  if (pct === null || pct === undefined) return "none";
  return pct > hi ? "high" : pct < lo ? "low" : "ok";
}

export function landscape(days) {
  const dates = [...new Set(days.map((d) => d.date))].sort();
  const places = [...new Set(days.map((d) => d.location_name || "Business"))].sort();
  const top = Math.max(1, ...days.map((d) => Math.max(Number(d.sales) || 0, costOf(d))));
  const scale = HEIGHT / top;
  const columns = days.map((d) => {
    const sales = Number(d.sales) || 0, costs = costOf(d), profit = sales - costs;
    const x = (dates.indexOf(d.date) - (dates.length - 1) / 2) * STEP_X;
    const z = (places.indexOf(d.location_name || "Business") - (places.length - 1) / 2) * STEP_Z;
    let y = 0;
    const segments = [];
    for (const p of PARTS) {
      const v = p.key === "profit" ? Math.max(0, profit) : Number(d[p.key]) || 0;
      if (v <= 0) continue;
      segments.push({ part: p.key, y0: y, h: v * scale });
      y += v * scale;
    }
    return { id: d.id, day: d, x, z, segments, height: Math.max(y, 0.04), salesAt: sales * scale, sales, costs, profit, loss: profit < 0 };
  });
  return { columns, dates, places, top, step: { x: STEP_X, z: STEP_Z }, size: { w: Math.max(1, dates.length) * STEP_X, d: Math.max(1, places.length) * STEP_Z } };
}
