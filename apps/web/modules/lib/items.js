/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Items for palettes and baskets: every active item of the business, with optional hints per item.
import { api } from "/assets/app.js";

const KIND_LABEL = { ingredient: "Ingredients", finished: "Products", supply: "Supplies" };

/** [{id, name, unit, kind, category}] - category falls back to the item type, so palettes always have groups. */
export async function catalogue(filter = () => true) {
  const s = await api("/stock/items").catch(() => ({ items: [] }));
  return s.items.filter(filter).map((i) => ({ ...i, category: i.category || KIND_LABEL[i.kind] || "Other" }));
}

/** Add a hint (e.g. "warehouse 12 kg") to palette items. */
export const withHints = (items, hint) => items.map((i) => ({ ...i, hint: hint(i) || i.unit }));

/** Basket lines from rows that name item_id, name, unit, a quantity and a hint. */
export const toLines = (rows, qty, hint = () => "") => rows.map((r) => ({ item_id: r.item_id, name: r.name || r.item_name, unit: r.unit, qty: qty(r) ?? "", hint: hint(r) }));

export const notFinished = (i) => i.kind !== "finished";
export const finished = (i) => i.kind === "finished";
