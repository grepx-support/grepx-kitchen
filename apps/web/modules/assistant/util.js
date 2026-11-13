/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the kitchen's assistant skills share: the business (currency, places), today, money in cents, and finding the
// item a question is about ("paneer", "naan") in a list of names.
import { biz } from "../lib/business.js";

export const business = () => biz();
export const currency = async () => (await biz()).business?.currency || "";
export const cents = (n) => (Number(n || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const thisMonth = () => new Date().toISOString().slice(0, 7);

/** The named thing a question is about, from [{name, ...}]: whole words first, then a part of a name. */
export function find(text, rows, key = "name") {
  const asked = String(text || "").toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter((w) => w.length > 2);
  let best = null, score = 0;
  for (const row of rows) {
    const name = String(row[key] || "").toLowerCase(), parts = name.split(/[^\p{L}\p{N}]+/u);
    let s = asked.reduce((n, w) => n + (parts.includes(w) ? 3 : parts.some((p) => p.startsWith(w) || w.startsWith(p) && p.length > 3) ? 2 : name.includes(w) ? 1 : 0), 0);
    if (s && parts.every((p) => !p || asked.includes(p))) s += 2;                 // every word of the name was asked: "paneer" is Paneer
    if (s > score || (s && s === score && name.length < String(best[key]).length)) { best = row; score = s; }
  }
  return best;
}
