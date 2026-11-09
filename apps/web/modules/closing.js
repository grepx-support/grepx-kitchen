/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Staff closing: few steps - count what you see, note issues, enter sales, check, submit (CLS-01..09).
import { api, esc, run } from "../../app.js";
import { biz, fmt, picker, remember, remembered } from "./lib.js";

const sells = (l) => !l.holding || l.kind !== "warehouse";

export const routes = [
  { path: "/closing", nav: "Closing", auth: "staff", perm: "closing", render: async function draw(el, q) {
    const b = await biz();
    const loc = q.location || remembered(b.locations, sells);
    if (!loc) { el.innerHTML = '<div class="card"><p>No location set up yet.</p></div>'; return; }
    remember(loc);
    const f = await api(`/closing/form?location_id=${loc}`);
    if (f.submitted_today) {
      el.innerHTML = `<h1>Closing</h1><div class="row"><div><label>Location</label>${picker(b.locations, loc, sells)}</div></div><div class="card"><h2 class="ok">Done for today ✓</h2><p>${esc(f.location.name)} was closed on ${esc(f.date)}.</p></div>`;
      el.querySelector("[data-pick]").onchange = (e) => draw(el, { location: e.target.value }); return;
    }
    el.innerHTML = `<h1>Closing</h1><form id="c">
      <div class="card"><div class="row"><div><label>Location</label>${picker(b.locations, loc, sells)}</div><div><label>Date</label><input name="date" type="date" value="${esc(f.date)}" max="${esc(f.date)}"></div>
        <div><label>Your name</label><input name="staff" value="${esc(f.staff_name)}" required></div></div>
        <p class="muted small">Counts every ${esc(f.location.count_every_days)} day(s)${f.last_closing ? ` · last closing ${esc(f.last_closing)}` : ""}</p></div><br>
      <div class="card"><h2>1. Count</h2><p class="muted">Type what you count. Leave a box empty if you did not count that item.</p>
        <table class="lines"><tr><th>Item</th><th>Expected</th><th>Counted</th></tr>${f.lines.map((l) => `<tr data-item="${esc(l.item_id)}"><td>${esc(l.item_name)}</td><td class="muted">${fmt(l.expected)} ${esc(l.unit)}</td>
          <td style="width:120px"><input type="number" inputmode="decimal" min="0" step="any" aria-label="Counted ${esc(l.item_name)}"></td></tr>`).join("")}</table></div><br>
      <div class="card"><h2>2. Sales</h2><div class="row">${f.sales_types.map((s) => `<div><label>${esc(s)}</label><input type="number" inputmode="decimal" min="0" step="0.01" data-sale="${esc(s)}"></div>`).join("")}</div></div><br>
      <div class="card"><h2>3. Issues</h2><textarea name="issues" rows="3" placeholder="Anything the owner should know (optional)"></textarea></div><br>
      <div class="card" id="review" hidden></div>
      <p><button class="btn primary" id="check" type="button">Check</button> <button class="btn primary" id="send" hidden>Submit closing</button></p></form>`;
    el.querySelector("[data-pick]").onchange = (e) => draw(el, { location: e.target.value });
    const form = el.querySelector("#c");
    const collect = () => ({ location_id: loc, date: form.date.value, staff_name: form.staff.value, issues: form.issues.value,
      counts: [...form.querySelectorAll("tr[data-item]")].map((tr) => ({ item_id: tr.dataset.item, qty: tr.querySelector("input").value })).filter((c) => c.qty !== "").map((c) => ({ ...c, qty: Number(c.qty) })),
      sales: Object.fromEntries([...form.querySelectorAll("[data-sale]")].filter((i) => i.value !== "").map((i) => [i.dataset.sale, Number(i.value)])) });
    el.querySelector("#check").onclick = () => {           // CLS-06: final check before submit
      const c = collect(); const names = Object.fromEntries(f.lines.map((l) => [l.item_id, l]));
      const total = Object.values(c.sales).reduce((a, n) => a + n, 0);
      const r = el.querySelector("#review");
      r.hidden = false;
      r.innerHTML = `<h2>Check before you submit</h2><p>${esc(c.staff_name)} · ${esc(c.date)} · ${c.counts.length} items counted · sales ${fmt(total)}</p>
        ${c.counts.map((x) => { const d = x.qty - (names[x.item_id]?.expected || 0); return `<div class="item">${esc(names[x.item_id]?.item_name)}: <b>${fmt(x.qty)}</b> <span class="${d < 0 ? "bad" : "ok"}">(${d > 0 ? "+" : ""}${fmt(d)} vs expected)</span></div>`; }).join("")}
        ${!total ? '<p class="bad">No sales entered.</p>' : ""}`;
      el.querySelector("#send").hidden = false;
    };
    form.onsubmit = async (e) => { e.preventDefault(); if (await run(() => api("/closing", { method: "POST", body: collect() }), "Closing submitted - thank you")) draw(el, { location: loc }); };
  } },
];
