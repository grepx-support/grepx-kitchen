/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Lots at a location, soonest expiry first, grouped by urgency: put each away in a bin, or throw it away.
import { api, run } from "/assets/app.js";
import { empty, html, kpiRow, pill } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { waste } from "../lib/waste.js";
import { frame, tone, when } from "./common.js";

const GROUPS = [["Expired", (d) => d !== null && d < 0], ["Use in 2 days", (d) => d !== null && d >= 0 && d <= 2],
  ["This week", (d) => d !== null && d > 2 && d <= 7], ["Later", (d) => d !== null && d > 7], ["No expiry date", (d) => d === null]];

export async function lots(el, q, b, place) {
  const f = await api(`/warehouse?location_id=${place}`);
  const body = frame(el, "lots", b, f.location_id, "Every delivery and batch, oldest expiry first - it leaves the warehouse in that order.");
  const count = (test) => f.lots.filter((l) => test(l.days_left)).length;
  body.innerHTML = String(html`${kpiRow([{ label: "Lots in stock", value: f.lots.length, icon: "box", area: "#0ea5e9" },
      { label: "Expired", value: count(GROUPS[0][1]), icon: "alert", area: "#e11d48", tone: count(GROUPS[0][1]) ? "bad" : "good" },
      { label: "Use in 2 days", value: count(GROUPS[1][1]), icon: "clock", area: "#f59e0b" },
      { label: "Not in a bin", value: f.lots.filter((l) => !l.bin_id).length, icon: "layout", area: "#8b5cf6", note: "put them away" }])}
    ${f.lots.length ? GROUPS.map(([title, test]) => { const rows = f.lots.filter((l) => test(l.days_left));
      return rows.length ? html`<section class="card k-section"><h2>${title} ${pill(String(rows.length), "info")}</h2><div class="k-lots">${rows.map((l) => html`
        <article class="k-lot ${tone(l.days_left)}"><div><b>${l.item_name}</b> <span class="muted">${fmt(l.qty)} ${l.unit}</span>
          <div class="small">${pill(when(l.days_left), tone(l.days_left))} ${l.lot_code ? pill(`lot ${l.lot_code}`) : ""} <span class="muted">in ${l.received}</span></div></div>
          <select data-bin="${l.id}" aria-label="Bin for ${l.item_name}"><option value="">No bin</option>${f.bins.map((x) => html`<option value="${x.id}" ${x.id === l.bin_id ? "selected" : ""}>${x.code} · ${x.zone}</option>`)}</select>
          <button class="btn small danger" data-waste="${l.id}">Throw away</button></article>`)}</div></section>` : ""; })
      : empty({ icon: "box", title: "No lots here yet", text: "Lots appear as stock is received, made or delivered." })}`);
  body.querySelectorAll("[data-bin]").forEach((s) => s.onchange = () => run(() => api(`/warehouse/lots/${s.dataset.bin}/move`, { method: "POST", body: { bin_id: s.value } }), "Put away"));
  body.querySelectorAll("[data-waste]").forEach((btn) => btn.onclick = async () => {
    const l = f.lots.find((x) => x.id === btn.dataset.waste);
    if (await waste({ location_id: f.location_id, item_id: l.item_id, name: `${l.item_name} (${when(l.days_left)})`, unit: l.unit, qty: l.qty, lot_id: l.id,
      reason: l.days_left !== null && l.days_left < 0 ? "expired" : "spoiled" })) lots(el, q, b, place);
  });
}
