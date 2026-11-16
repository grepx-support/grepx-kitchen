/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Barcode labels: shared by every business product - this is the platform copy (web/modules/business/lib/labels.js);
// here only what a kitchen's labels say: a lot from a supplier (expiry, batch, received), a batch the kitchen made
// (made on, use by, allergens), an item's shelf label. Scanning a lot label picks its item on any stock screen.
import { printLabelsDialog as print } from "/assets/modules/business/lib/labels.js";

export { LAYOUTS, labelsDocument, printLabels } from "/assets/modules/business/lib/labels.js";
export const printLabelsDialog = (items, opts = {}) => print(items, { price: false, ...opts });

const day = (iso) => { try { return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "2-digit" }); } catch (e) { return iso; } };
const plus = (iso, days) => { const d = new Date(`${iso}T00:00:00`); d.setDate(d.getDate() + Number(days)); return d.toISOString().slice(0, 10); };
const today = () => new Date().toISOString().slice(0, 10);

/** A lot's barcode: 12 letters / digits from a hash of its whole id (two 32-bit FNV-1a hashes) - short enough to scan on
 *  a 38 x 25 mm label; lots of one delivery share the start of their ids, so the whole id is hashed. */
export function lotCode(l) {
  const id = String(l.id || "");
  const fnv = (seed) => { let h = seed >>> 0; for (let i = 0; i < id.length; i++) { h ^= id.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h; };
  return (fnv(2166136261).toString(36).padStart(7, "0") + fnv(84696351).toString(36).padStart(7, "0")).slice(0, 12).toUpperCase();
}

/** A lot (warehouse /warehouse lots row) - scanning its label picks the lot's item. */
export const lotLabel = (l) => ({ code: lotCode(l), title: l.item_name, big: l.expiry ? `USE BY ${day(l.expiry).toUpperCase()}` : "",
  lines: [[l.lot_code ? `Lot ${l.lot_code}` : "", l.received ? `In ${day(l.received)}` : "", l.bin_code ? `Bin ${l.bin_code}` : ""].filter(Boolean).join(" · "),
    l.qty != null ? `${l.qty} ${l.unit || ""}` : ""].filter(Boolean) });

/** A batch the kitchen made today: made on, use by (the item's shelf life), allergens and the veg mark. */
export function batchLabel(item, { made = today(), batch = "", allergens = null, diet = null } = {}) {
  const contains = allergens ?? item.allergens ?? [];
  const mark = diet ?? item.diet ?? "";
  return { code: item.barcode || item.id, title: item.name, big: item.shelf_life_days != null ? `USE BY ${day(plus(made, item.shelf_life_days)).toUpperCase()}` : "",
    lines: [`Made ${day(made)}${batch ? ` · batch ${batch}` : ""}${mark ? ` · ${mark}` : ""}`, contains.length ? `Contains: ${contains.join(", ")}` : "No listed allergens"] };
}

/** An item's shelf / bin label: its own barcode, or its id when it has none (scans just the same). */
export const itemLabel = (item) => ({ code: item.barcode || item.id, title: item.name, lines: [[item.category, item.unit].filter(Boolean).join(" · ")] });

/** For a Builder: a scanned lot label -> its item (by lot id), so scanning a box on the shelf adds the right item. */
export const lotResolver = (items, lots) => (code) => {
  const key = String(code || "").toUpperCase();
  const lot = (lots || []).find((l) => lotCode(l) === key || l.id === code);
  return lot ? items.find((i) => i.id === lot.item_id) || null : items.find((i) => i.id === code) || null;
};
