/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Where each bin stands on the 3D floor, how tall it is and what colour - plain maths, no drawing.
// Zones become aisles (rows), bins stand along them in code order; lots without a bin sit on a "floor" pad.
export const CELL = 120, GAP = 44, MAX_H = 170;

const worst = (lots) => {
  const days = lots.map((l) => l.days_left).filter((d) => d !== null && d !== undefined);
  return days.length ? Math.min(...days) : null;
};

export const toneOf = (days) => (days === null ? "none" : days < 0 ? "bad" : days <= 2 ? "warn" : days <= 7 ? "info" : "good");

/** bins + open lots -> [{ id, code, zone, x, y, h, tone, lots, qty }] and the floor's size. */
export function layout(bins, lots) {
  const byBin = new Map();
  lots.forEach((l) => { const k = l.bin_id || ""; byBin.set(k, [...(byBin.get(k) || []), l]); });
  const slots = [...bins].sort((a, z) => a.code.localeCompare(z.code, undefined, { numeric: true }))
    .map((b) => ({ id: b.id, code: b.code, zone: b.zone || "other", lots: byBin.get(b.id) || [] }));
  if (byBin.has("")) slots.push({ id: "", code: "Floor", zone: "no bin", lots: byBin.get("") });
  const zones = [...new Set(slots.map((s) => s.zone))];
  const most = Math.max(1, ...slots.map((s) => s.lots.reduce((n, l) => n + l.qty, 0)));
  const rows = zones.map((z) => slots.filter((s) => s.zone === z));
  const placed = rows.flatMap((row, r) => row.map((s, c) => {
    const qty = s.lots.reduce((n, l) => n + l.qty, 0);
    return { ...s, qty, x: c * (CELL + GAP), y: r * (CELL + GAP * 2), h: qty ? 18 + (MAX_H - 18) * Math.sqrt(qty / most) : 6, tone: toneOf(worst(s.lots)) };
  }));
  const width = Math.max(1, ...rows.map((row) => row.length)) * (CELL + GAP) - GAP;
  return { boxes: placed, zones, width, depth: rows.length * (CELL + GAP * 2) - GAP * 2 };
}
