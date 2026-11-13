/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The 3D warehouse page: a WebGL scene of the racks (scene/*) with search, expiry / fill colours, a tour of the bins
// that need attention, pick-list routes, arrow-key moves between bins, snapshot, top view and full screen; the side
// panel shows what is in the chosen bin (or the open pick lists). No WebGL -> the simple view.
import { api } from "/assets/app.js";
import { html, icon, pill } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { frame, tone, when } from "./common.js";
import { flat3d } from "./flat3d.js";
import { neighbour, plan as makePlan } from "./scene/plan.js";
import { webglWorks } from "../lib/three/support.js";

const LEGEND = [["bad", "Expired"], ["warn", "2 days"], ["info", "A week"], ["good", "Fresh"], ["none", "No date"]];

const lotRow = (l) => html`<li><b>${l.item_name}</b><span>${fmt(l.qty)} ${l.unit}</span>${pill(when(l.days_left ?? null), tone(l.days_left ?? null))}</li>`;

function details(bay, found) {
  if (found) return html`<h3>${found.length} bin${found.length === 1 ? "" : "s"} with it</h3><ul class="w3d-found">${found.map((b) =>
    html`<li><button class="btn small" data-go="${b.id}">${b.code}</button><span class="muted">${b.zone}</span><b>${fmt(b.qty)}</b></li>`)}</ul>`;
  if (!bay) return html`<h3>Pick a bin</h3><p class="muted">Click a rack or pallet, search for an item, or press ${icon("play", { size: 14 })} to visit the bins that need attention.</p>`;
  const lots = [...bay.lots].sort((a, z) => (a.days_left ?? 999) - (z.days_left ?? 999));
  return html`<h3>${bay.code} <span class="muted small">${bay.zone}</span></h3>
    <div class="w3d-fill"><i style="width:${Math.round(bay.cartons.length / (bay.floor ? 12 : 18) * 100)}%"></i></div>
    <p class="muted small">${lots.length} lot${lots.length === 1 ? "" : "s"} · ${fmt(bay.qty)} in all</p>
    ${lots.length ? html`<ul class="w3-lots">${lots.map(lotRow)}</ul>` : html`<p class="muted">Empty.</p>`}`;
}

function picksPanel(picks, places, shown, stops) {
  if (!picks.length) return html`<h3>Pick lists</h3><p class="muted">No open pick lists here. Make one on the Pick lists tab.</p>`;
  return html`<h3>Pick lists</h3><ul class="w3d-picks">${picks.map((k) => html`<li class="${shown === k.id ? "on" : ""}">
    <div><b>To ${places[k.to_location_id] || "?"}</b><span class="muted small">${k.lines.length} line${k.lines.length === 1 ? "" : "s"} · ${k.by_name || ""}</span></div>
    <button class="btn small" data-route="${k.id}">${shown === k.id ? "Hide" : "Show route"}</button></li>`)}</ul>
    ${stops?.length ? html`<h3>Walk</h3><ol class="w3d-walk">${stops.map((st) => html`<li><button class="btn small" data-go="${st.bay.id}">${st.bay.code}</button>
      <span>${st.take.map((t) => `${t.name} ${fmt(t.qty)} ${t.unit || ""}`).join(", ")}</span></li>`)}</ol>` : ""}`;
}

function shell(p, picks) {
  const s = p.stats;
  return html`<div class="w3d">
    <div class="w3d-stage" data-stage tabindex="0" aria-label="3D warehouse - arrow keys move between bins, Enter shows one, Escape goes back">
      <div class="w3d-hud"><span>${icon("cube", { size: 15 })} ${s.bins} bins</span><span>${icon("box", { size: 15 })} ${s.lots} lots</span>
        ${s.expired ? html`<span class="bad">${icon("alert", { size: 15 })} ${s.expired} with expired stock</span>` : ""}
        ${s.soon ? html`<span class="warn">${icon("clock", { size: 15 })} ${s.soon} expiring soon</span>` : ""}</div>
      <div class="w3d-tools">
        <label class="w3d-search">${icon("search", { size: 16 })}<input data-q placeholder="Find an item" autocomplete="off"></label>
        <div class="w3d-seg"><button class="on" data-mode="expiry">Expiry</button><button data-mode="fill">Fill</button><button data-mode="plain">Cartons</button></div>
        <button class="w3d-btn w3d-count" data-picks title="Pick list routes">${icon("list", { size: 16 })}${picks.length ? html`<em>${picks.length}</em>` : ""}</button>
        <button class="w3d-btn" data-tour title="Tour the bins that need attention">${icon("play", { size: 16 })}</button>
        <button class="w3d-btn" data-spin title="Turn slowly">${icon("refresh", { size: 16 })}</button>
        <button class="w3d-btn" data-top title="View from above">${icon("layout", { size: 16 })}</button>
        <button class="w3d-btn" data-home title="Back to the start">${icon("home", { size: 16 })}</button>
        <button class="w3d-btn" data-snap title="Save a picture">${icon("camera", { size: 16 })}</button>
        <button class="w3d-btn" data-full title="Full screen">${icon("expand", { size: 16 })}</button></div>
      <div class="w3d-legend" data-legend>${LEGEND.map(([k, t]) => html`<button data-tone="${k}" class="${k}"><i></i>${t}</button>`)}</div>
      <div class="w3d-legend w3d-fill-legend" data-fill-legend hidden><span>Empty</span><i></i><span>Full</span></div>
      <div class="w3d-help">Drag to turn · right-drag to move · scroll to zoom · click a bin · arrow keys move</div>
      <div class="w3d-tip" data-tip hidden></div>
      <div class="w3d-loading" data-loading>${icon("cube", { size: 28 })}<span>Building the warehouse…</span></div>
    </div>
    <aside class="card w3-panel" data-panel>${details(null)}</aside></div>`;
}

class Controls {
  constructor(root, world, p, d) {
    Object.assign(this, { root, world, p, q: "", tone: null, picks: (d.picks || []).filter((k) => k.state !== "done"), places: d.places || {}, shown: null });
    this.panel = root.querySelector("[data-panel]");
    const on = (sel, fn) => root.querySelectorAll(sel).forEach((b) => b.addEventListener("click", () => fn(b)));
    on("[data-mode]", (b) => {
      root.querySelectorAll("[data-mode]").forEach((x) => x.classList.toggle("on", x === b));
      world.setMode(b.dataset.mode);
      root.querySelector("[data-legend]").hidden = b.dataset.mode === "fill";
      root.querySelector("[data-fill-legend]").hidden = b.dataset.mode !== "fill";
    });
    on("[data-picks]", () => { this.panel.innerHTML = String(picksPanel(this.picks, this.places, this.shown, this.stops)); });
    on("[data-snap]", () => Object.assign(document.createElement("a"), { href: world.snapshot(), download: "warehouse-3d.png" }).click());
    on("[data-tour]", (b) => { const go = !b.classList.contains("on"); b.classList.toggle("on", go); world.tour(go); });
    on("[data-spin]", (b) => world.spin(b.classList.toggle("on")));
    on("[data-top]", () => world.top());
    on("[data-home]", () => { world.select(null, false); world.home(); });
    on("[data-full]", () => (document.fullscreenElement ? document.exitFullscreen() : root.querySelector("[data-stage]").requestFullscreen?.()));
    on("[data-tone]", (b) => { this.tone = this.tone === b.dataset.tone ? null : b.dataset.tone; root.querySelectorAll("[data-tone]").forEach((x) => x.classList.toggle("on", x.dataset.tone === this.tone)); this.refocus(); });
    const input = root.querySelector("[data-q]");
    input.addEventListener("input", () => { this.q = input.value.trim().toLowerCase(); this.refocus(); });
    input.addEventListener("keydown", (e) => { if (e.key === "Enter" && this.found?.length) world.select(this.found[0].id); if (e.key === "Escape") { input.value = ""; this.q = ""; this.refocus(); } });
    this.panel.addEventListener("click", (e) => {
      const go = e.target.closest("[data-go]")?.dataset.go, route = e.target.closest("[data-route]")?.dataset.route;
      if (go) world.select(go, true, false);
      if (route) this.route(route);
    });
    const stage = root.querySelector("[data-stage]");
    stage.addEventListener("keydown", (e) => this.key(e));
    stage.addEventListener("pointerdown", () => stage.focus({ preventScroll: true }));
    world.stage.controls.addEventListener("start", () => root.querySelector("[data-tour]").classList.remove("on"));
  }

  route(id) {
    this.shown = this.shown === id ? null : id;
    this.stops = this.world.showRoute(this.picks.find((k) => k.id === this.shown) || null);
    this.panel.innerHTML = String(picksPanel(this.picks, this.places, this.shown, this.stops));
  }

  key(e) {
    if (e.target.closest("input")) return;
    if (e.key.startsWith("Arrow")) {
      e.preventDefault();
      e.stopPropagation();
      this.world.select(neighbour(this.p, this.world.chosen, e.key));
    } else if (e.key === "Escape") {
      this.world.select(null, false);
      this.world.home();
    }
  }

  refocus() {
    const match = (b) => (!this.q || b.lots.some((l) => (l.item_name || "").toLowerCase().includes(this.q))) && (!this.tone || b.tone === this.tone);
    this.found = this.q || this.tone ? this.p.bays.filter(match) : null;
    this.world.setFocus(this.found ? new Set(this.found.map((b) => b.id)) : null);
    this.panel.innerHTML = String(details(null, this.found));
  }
}

function tooltip(stage) {
  const tip = stage.querySelector("[data-tip]");
  return (bay, e) => {
    if (!bay || !e) { tip.hidden = true; return; }
    const r = stage.getBoundingClientRect();
    tip.innerHTML = String(html`<b>${bay.code}</b> <span>${bay.lots.length ? `${bay.lots.length} lot${bay.lots.length === 1 ? "" : "s"} · ${fmt(bay.qty)}` : "empty"}</span>`);
    Object.assign(tip.style, { left: `${e.clientX - r.left + 14}px`, top: `${e.clientY - r.top + 14}px` });
    tip.hidden = false;
  };
}

export async function view3d(el, q, b, place) {
  if (!webglWorks()) return flat3d(el, q, b, place);
  const d = await api(`/warehouse?location_id=${place}`);
  const p = makePlan(d.bins, d.lots);
  const body = frame(el, "3d", b, place, "Racks, shelves and cartons as they stand. Colour = the soonest expiry in the bin.");
  body.innerHTML = String(shell(p, (d.picks || []).filter((k) => k.state !== "done")));
  const root = body.querySelector(".w3d"), stage = root.querySelector("[data-stage]"), panel = root.querySelector("[data-panel]");
  const { Warehouse3D } = await import("./scene/world.js");
  const world = new Warehouse3D(stage, p, { onPick: (bay) => { panel.innerHTML = String(details(bay)); }, onHover: tooltip(stage) });
  new Controls(root, world, p, d);
  root.querySelector("[data-loading]").remove();
  if (!p.bays.length) panel.innerHTML = '<h3>Nothing here yet</h3><p class="muted">Add bins on the Bins tab and receive some stock to see it here.</p>';
}
