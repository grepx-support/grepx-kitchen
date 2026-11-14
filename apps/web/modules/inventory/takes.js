/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Stock takes: start one (blind = counters do not see what the system expects), count, finish -> stock corrected.
import { api, run } from "/assets/app.js";
import { html, icon, pill } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt, money, stamp } from "../lib/format.js";
import { picker } from "../lib/place.js";
import { frame } from "./common.js";

export async function takes(el) {
  const [b, d] = await Promise.all([biz(), api("/inventory/takes")]);
  const body = frame(el, "takes", "A full count of one location; the difference is corrected in stock and kept as variance.");
  body.innerHTML = String(html`<form class="card accent k-bar">${picker(b.locations, b.locations[0]?.id)}
      <label class="check"><input type="checkbox" name="blind" checked> Blind count</label><label class="check"><input type="checkbox" name="all"> Every item (not only those in stock)</label>
      <button class="btn primary">${icon("clipboard", { size: 16 })} Start stock take</button></form>
    <section class="card k-section"><h2>Stock takes</h2>${d.takes.map((t) => html`<a class="k-row" href="#/inventory/take/${t.id}"><b>${t.location_name}</b>
      <span>${stamp(t.started_at)} · ${t.started_by}${t.state === "done" ? ` · ${t.lines_changed} of ${t.lines_counted} changed` : ""}</span>
      ${t.state === "done" ? pill(money(b, t.variance_value), t.variance_value < 0 ? "bad" : "good") : pill(t.state, t.state === "open" ? "warn" : "")}</a>`)}
      ${d.takes.length ? "" : html`<p class="muted">None yet.</p>`}</section>`);
  body.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    const t = await run(() => api("/inventory/takes", { method: "POST", body: { location_id: body.querySelector("[data-pick]").value,
      blind: e.target.blind.checked, all_items: e.target.all.checked } }));
    if (t) location.hash = `#/inventory/take/${t.take_id}`;
  };
}

export async function take(el, id) {
  const [b, d] = await Promise.all([biz(), api("/inventory/takes")]);
  const t = d.takes.find((x) => x.id === id);
  const body = frame(el, "takes", t ? `${t.location_name} · started ${stamp(t.started_at)} by ${t.started_by}` : "");
  if (!t) { body.innerHTML = '<div class="card"><p>Not found.</p></div>'; return; }
  const open = t.state === "open";
  body.innerHTML = String(html`${open ? "" : html`<p>${pill(`Variance ${money(b, t.variance_value)}`, t.variance_value < 0 ? "bad" : "good")} ${pill(`${t.lines_changed} lines corrected`, "info")}</p>`}
    <div class="k-count">${t.lines.map((l) => html`<label class="${l.counted !== null && l.counted !== undefined ? "done" : ""}">${l.name}
      <small>${open ? (t.blind ? l.unit : `expected ${fmt(l.expected)} ${l.unit}`) : `expected ${fmt(l.expected)} · counted ${fmt(l.counted)} · ${l.variance > 0 ? "+" : ""}${fmt(l.variance)}`}</small>
      ${open ? html`<input type="number" inputmode="decimal" min="0" step="any" data-item="${l.item_id}" value="${l.counted ?? ""}">` : html`<b class="${l.variance < 0 ? "bad" : "ok"}">${l.value ? money(b, l.value) : ""}</b>`}</label>`)}</div>
    ${open ? html`<div class="k-nav"><button class="btn" data-save>Save counts</button><span><button class="btn" data-cancel>Cancel</button>
      <button class="btn primary" data-finish>${icon("check", { size: 16 })} Finish and correct stock</button></span></div>` : ""}`);
  const lines = () => [...body.querySelectorAll("[data-item]")].map((i) => ({ item_id: i.dataset.item, qty: i.value }));
  const save = () => run(() => api(`/inventory/takes/${id}/count`, { method: "POST", body: { lines: lines() } }));
  body.querySelectorAll("[data-item]").forEach((i) => i.oninput = () => i.closest("label").classList.toggle("done", i.value !== ""));
  body.querySelector("[data-save]")?.addEventListener("click", () => save().then((r) => r && take(el, id)));
  body.querySelector("[data-finish]")?.addEventListener("click", async () => {
    if ((await save()) && await run(() => api(`/inventory/takes/${id}/finish`, { method: "POST" }), "Stock corrected")) take(el, id);
  });
  body.querySelector("[data-cancel]")?.addEventListener("click", async () => { if (await run(() => api(`/inventory/takes/${id}/cancel`, { method: "POST" }))) location.hash = "#/inventory/takes"; });
}
