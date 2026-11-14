/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Cost days come one per location; charts of the whole business want one point per date.

const pctOf = (part, whole) => (whole > 0 ? Math.round((part / whole) * 1000) / 10 : null);

/** [{date, sales, ingredient_cost, labour, rent, other, cogs_pct, costing_pct}] - one per date, oldest first. */
export function byDay(days) {
  const out = new Map();
  for (const d of days) {
    const t = out.get(d.date) || { date: d.date, sales: 0, ingredient_cost: 0, labour: 0, rent: 0, other: 0 };
    for (const k of ["sales", "ingredient_cost", "labour", "rent", "other"]) t[k] += Number(d[k] || 0);
    out.set(d.date, t);
  }
  return [...out.values()].sort((a, b) => a.date.localeCompare(b.date)).map((t) => ({ ...t,
    cogs_pct: pctOf(t.ingredient_cost, t.sales), costing_pct: pctOf(t.ingredient_cost + t.labour + t.rent + t.other, t.sales) }));
}
