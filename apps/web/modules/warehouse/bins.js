/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Bins, shelves, fridges and freezers of a location, by zone.
import { api, run } from "/assets/app.js";
import { html } from "/assets/kit/index.js";
import { frame } from "./common.js";

const ZONES = [["dry", "Dry store", "#f59e0b"], ["chilled", "Chiller", "#0ea5e9"], ["frozen", "Freezer", "#6366f1"], ["packaging", "Packaging", "#94a3b8"]];

export async function bins(el, q, b, place) {
  const f = await api(`/warehouse?location_id=${place}`);
  const body = frame(el, "bins", b, f.location_id, "Where things are kept - pick lists walk the bins in order.");
  const inBin = (id) => f.lots.filter((l) => l.bin_id === id).length;
  body.innerHTML = String(html`<div class="grid">${ZONES.map(([z, label, color]) => html`<section class="card accent" style="--area:${color}"><h2>${label}</h2>
      ${f.bins.filter((x) => x.zone === z).map((x) => html`<div class="k-row"><b>${x.code}</b><span>${x.note || ""}</span><span class="badge">${inBin(x.id)} lots</span></div>`)}
      ${f.bins.some((x) => x.zone === z) ? "" : html`<p class="muted">None yet.</p>`}</section>`)}</div>
    <form class="card accent k-section"><h2>Add a bin</h2><div class="row"><label>Code<input name="code" required placeholder="A-01"></label>
      <label>Zone<select name="zone">${ZONES.map(([z, label]) => html`<option value="${z}">${label}</option>`)}</select></label>
      <label>Note<input name="note" placeholder="top shelf, left"></label></div><p><button class="btn primary">Add bin</button></p></form>`);
  body.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    const d = new FormData(e.target);
    if (await run(() => api("/warehouse/bins", { method: "POST", body: { location_id: f.location_id, code: d.get("code"), zone: d.get("zone"), note: d.get("note") } }), "Bin added")) bins(el, q, b, place);
  };
}
