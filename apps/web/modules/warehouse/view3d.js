/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The 3D warehouse: CSS 3D boxes on a floor you can spin (drag), tilt, zoom (wheel / pinch buttons) and click.
// Geometry comes from layout3d.js; this file only builds faces and handles the camera.
import { api } from "/assets/app.js";
import { html, icon, pill } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { frame, tone, when } from "./common.js";
import { CELL, layout } from "./layout3d.js";

const LEGEND = [["bad", "Expired"], ["warn", "Expires in 2 days"], ["info", "Within a week"], ["good", "Fresh"], ["none", "Empty / no date"]];

/** A box: five faces (no bottom), each a div placed with a 3D transform. */
const box = (b) => html`<div class="w3-box ${b.tone}" data-bin="${b.id}" style="--x:${b.x}px;--y:${b.y}px;--h:${b.h}px;--w:${CELL}px" tabindex="0"
  role="button" aria-label="Bin ${b.code}, ${b.lots.length} lots">
  <i class="f top"><b>${b.code}</b></i><i class="f front"></i><i class="f back"></i><i class="f left"></i><i class="f right"></i></div>`;

class Camera {
  constructor(world) { Object.assign(this, { world, spin: -38, tilt: 58, zoom: 0.9, auto: false }); this.apply(); }
  apply() {
    this.world.style.setProperty("--spin", `${this.spin}deg`);
    this.world.style.setProperty("--tilt", `${this.tilt}deg`);
    this.world.style.setProperty("--zoom", this.zoom);
  }
  turn(dx, dy) { this.spin += dx * 0.35; this.tilt = Math.min(80, Math.max(20, this.tilt - dy * 0.25)); this.apply(); }
  scale(k) { this.zoom = Math.min(1.8, Math.max(0.4, this.zoom * k)); this.apply(); }
  reset() { Object.assign(this, { spin: -38, tilt: 58, zoom: 0.9 }); this.apply(); }
}

function details(b) {
  if (!b) return html`<p class="muted">Click a bin to see what is in it.</p>`;
  return html`<h3>${b.code} <span class="muted small">${b.zone}</span></h3>${b.lots.length ? html`<ul class="w3-lots">${b.lots
    .sort((a, z) => (a.days_left ?? 999) - (z.days_left ?? 999)).map((l) => html`<li><b>${l.item_name}</b><span>${fmt(l.qty)} ${l.unit}</span>
      ${pill(when(l.days_left), tone(l.days_left))}</li>`)}</ul>` : html`<p class="muted">Empty.</p>`}`;
}

function wire(stage, cam, plan, panel) {
  let last = null;
  stage.onpointerdown = (e) => { if (e.target.closest("button")) return; last = [e.clientX, e.clientY]; stage.setPointerCapture(e.pointerId); cam.auto = false; };
  stage.onpointermove = (e) => { if (!last) return; cam.turn(e.clientX - last[0], e.clientY - last[1]); last = [e.clientX, e.clientY]; };
  stage.onpointerup = () => { last = null; };
  stage.onwheel = (e) => { e.preventDefault(); cam.scale(e.deltaY < 0 ? 1.08 : 0.93); };
  const pick = (el) => {
    stage.querySelectorAll(".w3-box.on").forEach((x) => x.classList.remove("on"));
    el.classList.add("on");
    panel.innerHTML = String(details(plan.boxes.find((b) => b.id === el.dataset.bin)));
  };
  stage.onclick = (e) => { const el = e.target.closest("[data-bin]"); if (el) pick(el); };
  stage.onkeydown = (e) => { if (e.key === "Enter" && e.target.dataset.bin !== undefined) pick(e.target); };
  stage.querySelector("[data-in]").onclick = () => cam.scale(1.15);
  stage.querySelector("[data-out]").onclick = () => cam.scale(0.87);
  stage.querySelector("[data-reset]").onclick = () => cam.reset();
  stage.querySelector("[data-auto]").onclick = () => { cam.auto = !cam.auto; };
  const spin = () => { if (!stage.isConnected) return; if (cam.auto) cam.turn(0.6, 0); requestAnimationFrame(spin); };
  spin();
}

export async function view3d(el, q, b, place) {
  const d = await api(`/warehouse?location_id=${place}`);
  const plan = layout(d.bins, d.lots);
  const body = frame(el, "3d", b, place, "Drag to turn, scroll to zoom, click a bin. Taller = more stock; colour = the soonest expiry in it.");
  body.innerHTML = String(html`<div class="w3">
    <div class="w3-stage" data-stage><div class="w3-world" style="--fw:${plan.width}px;--fd:${plan.depth}px">
      <div class="w3-floor"></div>${plan.boxes.map(box)}</div>
      <div class="w3-ctl"><button class="kit-iconbtn" data-in aria-label="Zoom in">${icon("plus")}</button><button class="kit-iconbtn" data-out aria-label="Zoom out">${icon("minus")}</button>
        <button class="kit-iconbtn" data-reset aria-label="Reset view">${icon("refresh")}</button><button class="kit-iconbtn" data-auto aria-label="Turn by itself">${icon("play")}</button></div>
      <div class="w3-legend">${LEGEND.map(([k, t]) => html`<span class="${k}"><i></i>${t}</span>`)}</div></div>
    <aside class="card w3-panel" data-panel>${details(null)}</aside></div>`);
  if (!plan.boxes.length) { body.querySelector("[data-panel]").innerHTML = '<p class="muted">No bins or stock here yet.</p>'; }
  const stage = body.querySelector("[data-stage]");
  wire(stage, new Camera(stage.querySelector(".w3-world")), plan, body.querySelector("[data-panel]"));
}
