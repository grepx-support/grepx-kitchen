/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Forecast: what each place will sell of each product, day by day (forecast-service), the method that fitted each
// product best and how right past forecasts were - and, for the owner, "use as this week's targets" for the kitchen.
import { api, can, run } from "/assets/app.js";
import { html, icon, kpiRow, pageHead, pill, raw } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { fmt } from "../lib/format.js";
import { spark } from "./spark.js";

const DAYS = [7, 14, 28];
const day = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: "short", day: "numeric" });
const errTone = (e) => (e === null || e === undefined ? "" : e <= 15 ? "good" : e <= 35 ? "warn" : "bad");

function controls(d, q) {
  const places = [...new Map(d.rows.map((r) => [r.location_id, r.location_name])).entries()];
  const link = (extra) => `#/kitchen/forecast?${new URLSearchParams({ ...q, ...extra })}`;
  return html`<div class="fc-controls"><div class="kit-chips">${DAYS.map((n) => html`<a class="kit-chip ${Number(q.days || 7) === n ? "on" : ""}" href="${link({ days: n })}">${n} days</a>`)}</div>
    <select data-q="method" aria-label="Method"><option value="auto">Best method per product</option>${d.methods.map((m) => html`<option value="${m.key}" ${q.method === m.key ? "selected" : ""}>${m.label}</option>`)}</select>
    ${places.length > 1 || q.location_id ? html`<select data-q="location_id" aria-label="Place"><option value="">Every place</option>${places.map(([id, name]) => html`<option value="${id}" ${q.location_id === id ? "selected" : ""}>${name}</option>`)}</select>` : ""}</div>`;
}

function make(d, owner) {
  if (!d.products.length) return html`<p class="muted">Nothing sold yet - forecasts start after the first closings.</p>`;
  return html`<table class="m-view fc-make"><thead><tr>${owner ? html`<th><input type="checkbox" data-all checked aria-label="All"></th>` : ""}<th>Product</th>
      <th class="end">Tomorrow</th><th class="end">Next ${d.days.length} days</th></tr></thead>
    <tbody>${d.products.map((p) => html`<tr>${owner ? html`<td><input type="checkbox" data-item="${p.item_id}" data-qty="${p.total}" checked></td>` : ""}
      <td><b>${p.name}</b></td><td class="end">${fmt(p.first_day)} ${p.unit}</td><td class="end"><b>${fmt(p.total)}</b> ${p.unit}</td></tr>`)}</tbody></table>
    ${owner ? html`<div class="fc-use"><button class="btn primary" data-use>${icon("check", { size: 16 })} Use as this week's kitchen targets</button>
      <span class="muted small">Sets each ticked product's target for this week to its forecast (rounded up). You can still change any on the Kitchen screen.</span></div>` : ""}`;
}

const card = (r, methods) => html`<article class="card fc-card"><header><div><b>${r.name}</b><span class="muted small">${r.location_name}</span></div>
    ${pill(r.error === null ? "not tested yet" : `${r.error}% off`, errTone(r.error))}</header>
  ${raw(spark(r.history, r.forecast))}
  <div class="fc-days">${r.forecast.slice(0, 7).map((f) => html`<span><small>${day(f.date)}</small><b>${fmt(f.qty)}</b></span>`)}</div>
  <p class="muted small">${methods[r.method] || r.method} · ${fmt(r.total)} ${r.unit} in ${r.forecast.length} days</p></article>`;

function accuracy(rows) {
  if (!rows.length) return html`<p class="muted small">Past forecasts are kept every day from now on; their accuracy shows here after a day.</p>`;
  const top = Math.max(1, ...rows.flatMap((r) => [r.forecast, r.actual]));
  return html`<div class="fc-acc">${rows.map((r) => html`<div title="${r.date}: forecast ${r.forecast}, sold ${r.actual}">
    <div class="bars"><i class="f" style="height:${(r.forecast / top) * 100}%"></i><i class="a" style="height:${(r.actual / top) * 100}%"></i></div>
    <small>${day(r.date)}</small>${pill(r.error === null ? "-" : `${r.error}%`, errTone(r.error))}</div>`)}</div>
    <div class="fc-legend"><span><i class="f"></i>Forecast</span><span><i class="a"></i>Sold</span></div>`;
}

export async function forecast(el, q) {
  const d = await api(`/forecast?${new URLSearchParams({ days: q.days || 7, method: q.method || "auto", location_id: q.location_id || "" })}`);
  const owner = can("manage_business"), methods = Object.fromEntries(d.methods.map((m) => [m.key, m.label]));
  const tested = d.rows.filter((r) => r.error !== null), avgErr = tested.length ? tested.reduce((n, r) => n + r.error, 0) / tested.length : null;
  el.style.setProperty("--area", area("kitchen"));
  el.innerHTML = String(html`${pageHead({ ...head("kitchen"), title: "Forecast", subtitle: "What each place will sell, learnt from its counts and sales - the best-fitting method for each product." })}
    ${controls(d, q)}
    ${kpiRow([{ label: "Products", value: d.products.length, icon: "pot", area: "#f97316" },
      { label: "Tomorrow, all places", value: fmt(d.products.reduce((n, p) => n + p.first_day, 0)), icon: "clock", area: "#7c3aed" },
      { label: `Next ${d.days.length} days`, value: fmt(d.products.reduce((n, p) => n + p.total, 0)), icon: "trend", area: "#0ea5e9" },
      { label: "Typical error (tested)", value: avgErr === null ? "-" : `${avgErr.toFixed(0)}%`, icon: "chart", area: "#16a34a" }])}
    <section class="card k-section"><h2>What to make</h2>${make(d, owner)}</section>
    <section class="fc-grid">${d.rows.map((r) => card(r, methods))}</section>
    <section class="card k-section"><h2>How right were past forecasts?</h2>${accuracy(d.accuracy)}</section>`);
  el.querySelectorAll("[data-q]").forEach((s) => s.onchange = () => { location.hash = `#/kitchen/forecast?${new URLSearchParams({ ...q, [s.dataset.q]: s.value })}`; });
  el.querySelector("[data-all]")?.addEventListener("change", (e) => el.querySelectorAll("[data-item]").forEach((c) => { c.checked = e.target.checked; }));
  el.querySelector("[data-use]")?.addEventListener("click", async () => {
    const items = Object.fromEntries([...el.querySelectorAll("[data-item]:checked")].map((c) => [c.dataset.item, Number(c.dataset.qty)]));
    if (!Object.keys(items).length) return;
    await run(() => api("/forecast/targets", { method: "POST", body: { items } }), `${Object.keys(items).length} targets set for this week`);
  });
}
