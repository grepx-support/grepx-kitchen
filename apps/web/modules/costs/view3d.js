/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The cost landscape section of the Costs page: the 3D scene (loaded only when shown), its controls, a tooltip and the
// chosen day's breakdown. Without WebGL the section says so and the charts below still tell the story.
import { html, icon } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { webglWorks } from "../lib/three/support.js";
import { PARTS, cogsTone, landscape } from "./landscape.js";

const hex = (n) => `#${n.toString(16).padStart(6, "0")}`;
const pct = (v) => (v === null || v === undefined ? "-" : `${Number(v).toFixed(1)}%`);
const TONE_WORD = { ok: "in range", high: "too high", low: "very low", none: "no count" };

function breakdown(c, range, cur) {
  if (!c) return html`<p class="muted">Click a column to see that day. Taller = more sales; the colours show where the money went.</p>`;
  const d = c.day, tone = cogsTone(d.cogs_pct, range);
  return html`<div class="c3-day"><div><b>${d.location_name}</b> <span class="muted">${d.date}${d.period_days > 1 ? ` (${d.period_days} days)` : ""}</span></div>
    <div class="c3-parts">${PARTS.map((p) => {
      const v = p.key === "profit" ? c.profit : Number(d[p.key]) || 0;
      return html`<span><i style="background:${hex(p.key === "profit" && v < 0 ? 0xe11d48 : p.colour)}"></i>${p.key === "profit" && v < 0 ? "Loss" : p.label}<b>${cur} ${fmt(Math.abs(v))}</b></span>`;
    })}</div>
    <div class="muted small">Sales ${cur} ${fmt(c.sales)} · COGS <b class="${tone === "ok" ? "good" : "bad"}">${pct(d.cogs_pct)}</b> (${TONE_WORD[tone]})</div></div>`;
}

export async function costLandscape(section, days, s, cur) {
  if (!days.length) { section.innerHTML = String(html`<h2>${icon("cube")} Cost landscape</h2><p class="muted">No closings this month yet.</p>`); return; }
  if (!webglWorks()) { section.innerHTML = String(html`<h2>${icon("cube")} Cost landscape</h2><p class="muted">This browser cannot show 3D.</p>`); return; }
  const plan = landscape(days), range = s.cogs_range || [25, 35];
  section.innerHTML = String(html`<div class="c3-head"><h2>${icon("cube")} Cost landscape</h2>
      <div class="c3-tools"><div class="w3d-seg"><button class="on" data-mode="split">Where it went</button><button data-mode="cogs">COGS %</button></div>
        <select data-place aria-label="Place"><option value="">Every place</option>${plan.places.map((p) => html`<option>${p}</option>`)}</select>
        <button class="w3d-btn" data-spin title="Turn slowly">${icon("refresh", { size: 16 })}</button>
        <button class="w3d-btn" data-home title="Back to the start">${icon("home", { size: 16 })}</button>
        <button class="w3d-btn" data-full title="Full screen">${icon("expand", { size: 16 })}</button></div></div>
    <div class="c3-stage w3d-stage" data-stage><div class="w3d-tip" data-tip hidden></div>
      <div class="w3d-legend c3-legend" data-legend-split>${PARTS.map((p) => html`<span><i style="background:${hex(p.colour)}"></i>${p.label}</span>`)}<span><i style="background:#ff2d55"></i>Sales line (loss)</span></div>
      <div class="w3d-legend c3-legend" data-legend-cogs hidden><span><i style="background:#22c55e"></i>COGS ${range[0]}-${range[1]}%</span><span><i style="background:#e11d48"></i>Above</span><span><i style="background:#3b82f6"></i>Below</span></div>
      <div class="w3d-help">Drag to turn · scroll to zoom · click a column</div></div>
    <div class="c3-panel" data-panel>${breakdown(null)}</div>`);
  const stage = section.querySelector("[data-stage]"), tip = section.querySelector("[data-tip]"), panel = section.querySelector("[data-panel]");
  const { CostLandscape } = await import("./scene3d.js");
  const world = new CostLandscape(stage, plan, { range,
    onPick: (c) => { panel.innerHTML = String(breakdown(c, range, cur)); },
    onHover: (c, e) => {
      if (!c || !e) { tip.hidden = true; return; }
      const r = stage.getBoundingClientRect();
      tip.innerHTML = String(html`<b>${c.day.location_name}</b> <span>${c.day.date} · ${cur} ${fmt(c.sales)} · ${c.loss ? "loss" : "left"} ${fmt(Math.abs(c.profit))}</span>`);
      Object.assign(tip.style, { left: `${e.clientX - r.left + 14}px`, top: `${e.clientY - r.top + 14}px` });
      tip.hidden = false;
    } });
  section.querySelectorAll("[data-mode]").forEach((b) => b.onclick = () => {
    section.querySelectorAll("[data-mode]").forEach((x) => x.classList.toggle("on", x === b));
    world.setMode(b.dataset.mode);
    section.querySelector("[data-legend-split]").hidden = b.dataset.mode !== "split";
    section.querySelector("[data-legend-cogs]").hidden = b.dataset.mode !== "cogs";
  });
  section.querySelector("[data-place]").onchange = (e) => world.setPlace(e.target.value || null);
  section.querySelector("[data-spin]").onclick = (e) => world.spin(e.currentTarget.classList.toggle("on"));
  section.querySelector("[data-home]").onclick = () => { world.select(null); world.home(); };
  section.querySelector("[data-full]").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : stage.requestFullscreen?.());
}
