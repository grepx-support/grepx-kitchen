/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Stock at every location (bars per location, negative stock in red) and the full movement history.
import { api } from "/assets/app.js";
import { barList, DataTable, h, html, kpiRow } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { biz } from "../lib/business.js";
import { fmt, stamp, today } from "../lib/format.js";
import { frame } from "./common.js";

export async function levels(el, q) {
  const b = await biz();
  const loc = q.location ?? "";
  const [s, m] = await Promise.all([api(`/stock${loc ? `?location_id=${loc}` : ""}`), api(`/stock/movements?limit=200${loc ? `&location_id=${loc}` : ""}`)]);
  const body = frame(el, "levels", { title: "Stock", subtitle: "What is where right now, and every change behind it." });
  const negative = s.levels.filter((r) => r.qty < 0).length;
  const places = [...new Set(s.levels.map((r) => r.location_name))];
  body.innerHTML = String(html`<div class="kit-chips k-bar"><a class="kit-chip ${loc ? "" : "on"}" href="#/stock">All locations</a>${b.locations.map((l) =>
      html`<a class="kit-chip ${l.id === loc ? "on" : ""}" href="#/stock?location=${l.id}">${l.name}</a>`)}</div>
    ${kpiRow([{ label: "Items held", value: new Set(s.levels.map((r) => r.item_id)).size, icon: "box", area: area("stock") },
      { label: "Locations", value: places.length, icon: "pin", area: area("deliveries") },
      { label: "Moves today", value: m.movements.filter((x) => x.date === today()).length, icon: "swap", area: area("move") },
      { label: "Below zero", value: negative, icon: "alert", area: negative ? "#e11d48" : "#16a34a", tone: negative ? "bad" : "good", note: negative ? "count these again" : "all fine" }])}
    <div class="grid">${places.map((p) => html`<section class="card accent"><h2>${p}</h2>${barList({ rows: s.levels.filter((r) => r.location_name === p)
      .map((r) => ({ label: `${r.item_name}`, value: r.qty, unit: ` ${r.unit}`, color: r.qty < 0 ? "#e11d48" : area("stock") })) })}</section>`)}</div>
    <section class="card k-section"><h2>History</h2><p class="muted small">Every change with who, when and why. Nobody can edit it.</p><div class="hist"></div></section>`);
  if (!places.length) body.querySelector(".grid").append(h("p", { class: "muted" }, "No stock recorded yet."));
  new DataTable({ rows: m.movements, columns: [
    { key: "at", label: "When", render: (r) => html`${stamp(r.at)}` },
    { key: "kind", label: "What", render: (r) => html`<b>${r.kind.replace("_", " ")}</b> <span class="muted small">${r.location_name || ""}${r.other_location_name ? ` ↔ ${r.other_location_name}` : ""}</span>${r.note ? html`<div class="muted small">${r.note}</div>` : ""}` },
    { key: "item_name", label: "Item" },
    { key: "qty", label: "Change", align: "end", render: (r) => html`<b class="${r.qty < 0 ? "bad" : "ok"}">${r.qty > 0 ? "+" : ""}${fmt(r.qty)}</b>` },
    { key: "user_name", label: "By" }] }).mount(body.querySelector(".hist"));
}
