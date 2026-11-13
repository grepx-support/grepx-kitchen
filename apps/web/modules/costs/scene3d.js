/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The cost landscape drawn: stacked columns (one instanced mesh per part), day and place labels, a red line where
// sales stopped on a loss-making day, columns growing in when it opens. Modes: "split" (where the money went) or
// "cogs" (each column one colour: COGS in range, too high, too low). Hover / click a column; fade all but one place.
import { Stage, THREE } from "../lib/three/stage.js";
import { Flight } from "../lib/three/flight.js";
import { Picker } from "../lib/three/picker.js";
import { tag } from "../lib/three/labels.js";
import { PARTS, cogsTone } from "./landscape.js";

const COGS = { ok: 0x22c55e, high: 0xe11d48, low: 0x3b82f6, none: 0x94a3b8 };
const W = 0.82;

class Bars {
  /** One instanced mesh of unit boxes; each instance placed and stretched to (x, y0, z, h). */
  constructor(rows, colour, material) {
    this.rows = rows;
    this.mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(W, 1, W), material, Math.max(1, rows.length));
    this.mesh.count = rows.length;
    this.mesh.castShadow = this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;           // its instances grow after the first frame, so its first bounds would be wrong
    this.base = rows.map((r) => new THREE.Color(r.colour ?? colour));
    this.grow(1);
    this.paint(() => true);
  }
  grow(k) {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
    this.rows.forEach((r, i) => {
      const f = Math.min(1, Math.max(0.0001, typeof k === "function" ? k(r) : k));
      m.compose(p.set(r.x, (r.y0 + r.h / 2) * f, r.z), q, s.set(1, Math.max(r.h * f, 0.0001), 1));
      this.mesh.setMatrixAt(i, m);
    });
    this.mesh.instanceMatrix.needsUpdate = true;
  }
  paint(lit, dark = false) {
    const faded = new THREE.Color(dark ? 0x1e293b : 0xd5dde8);
    this.rows.forEach((r, i) => this.mesh.setColorAt(i, lit(r) ? this.base[i] : this.base[i].clone().lerp(faded, 0.88)));
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
  }
}

export class CostLandscape {
  constructor(host, plan, { range, onPick = () => {}, onHover = () => {} }) {
    const stage = this.stage = new Stage(host);
    Object.assign(this, { plan, range, onPick, place: null, mode: "split" });
    stage.fit(plan.size.w + 4, plan.size.d + 4);
    const mat = () => new THREE.MeshStandardMaterial({ roughness: 0.45, metalness: 0.15 });
    this.parts = PARTS.map((p) => new Bars(plan.columns.flatMap((c) => c.segments.filter((s) => s.part === p.key)
      .map((s) => ({ ...s, x: c.x, z: c.z, column: c }))), p.colour, mat()));
    this.whole = new Bars(plan.columns.map((c) => ({ x: c.x, z: c.z, y0: 0, h: Math.max(c.salesAt, 0.04), column: c,
      colour: COGS[cogsTone(c.day.cogs_pct, range)] })), 0xffffff, mat());
    this.whole.mesh.visible = false;
    this.hits = new THREE.InstancedMesh(new THREE.BoxGeometry(W + 0.1, 1, W + 0.1), new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }), Math.max(1, plan.columns.length));
    plan.columns.forEach((c, i) => this.hits.setMatrixAt(i, new THREE.Matrix4().compose(new THREE.Vector3(c.x, c.height / 2, c.z), new THREE.Quaternion(), new THREE.Vector3(1, c.height + 0.2, 1))));
    this.hits.count = plan.columns.length;
    stage.scene.add(...this.parts.map((b) => b.mesh), this.whole.mesh, this.hits, this.ground(), this.lossLines(), this.labels(), this.outline());
    this.flight = new Flight(stage);
    new Picker(stage, [this.hits], { idOf: (h) => h.instanceId ?? null,
      hover: (i, e) => onHover(i === null ? null : plan.columns[i], e), pick: (i) => this.select(i) });
    const r = Math.max(plan.size.w, plan.size.d * 1.6) * 0.62 + 6;
    stage.camera.position.set(0, r * 1.6, r * 1.8);
    this.home(1.8);
    this.growIn();
  }

  ground() {
    const g = new THREE.Group(), w = this.plan.size.w + 8, d = this.plan.size.d + 8, dark = this.stage.dark;
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshStandardMaterial({ color: dark ? 0x111a2e : 0xe2e8f0, roughness: 0.95 }));
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    const grid = new THREE.GridHelper(Math.max(w, d), Math.round(Math.max(w, d) / this.plan.step.x), dark ? 0x334155 : 0xcbd5e1, dark ? 0x1e293b : 0xdbe3ee);
    grid.position.y = 0.005;
    g.add(floor, grid);
    return g;
  }

  lossLines() {
    const g = new THREE.Group(), geo = new THREE.BoxGeometry(W + 0.16, 0.05, W + 0.16), mat = new THREE.MeshBasicMaterial({ color: 0xff2d55 });
    this.plan.columns.filter((c) => c.loss).forEach((c) => { const m = new THREE.Mesh(geo, mat); m.position.set(c.x, c.salesAt, c.z); g.add(m); });
    return g;
  }

  labels() {
    const g = new THREE.Group(), { dates, places, size, step } = this.plan, every = Math.max(1, Math.ceil(dates.length / 12));
    dates.forEach((d, i) => {
      if (i % every) return;
      const t = tag(d.slice(5), 0.32, { bg: "rgba(15,23,42,.8)" });
      t.position.set((i - (dates.length - 1) / 2) * step.x, 0.25, size.d / 2 + 0.9);
      g.add(t);
    });
    places.forEach((p, i) => {
      const t = tag(p, 0.42, { bg: "rgba(124,58,237,.92)" });
      t.position.set(-size.w / 2 - 0.4 - t.scale.x / 2, 0.6, (i - (places.length - 1) / 2) * step.z);
      g.add(t);
    });
    return g;
  }

  outline() {
    this.box = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), new THREE.LineBasicMaterial({ color: 0x22d3ee, depthTest: false }));
    this.box.renderOrder = 10;
    this.box.visible = false;
    return this.box;
  }

  growIn() {
    const t0 = performance.now(), n = this.plan.dates.length || 1;
    let on = true;
    const delay = (c) => (this.plan.dates.indexOf(c.day.date) / n) * 0.8;
    this.stage.onFrame(() => {
      if (!on) return;
      const t = (performance.now() - t0) / 1000, ease = (k) => 1 - (1 - k) ** 3;
      const f = (r) => ease(Math.min(1, Math.max(0, (t - delay(r.column)) / 0.7)));
      [...this.parts, this.whole].forEach((b) => b.grow(f));
      if (t > 1.6) { on = false; [...this.parts, this.whole].forEach((b) => b.grow(1)); }
    });
  }

  home(seconds = 1.2) {
    const r = Math.max(this.plan.size.w, this.plan.size.d * 1.6) * 0.62 + 6;
    return this.flight.to([0, 2, 0], [r * 0.35, r * 0.6, r * 0.95], seconds);
  }

  select(i) {
    const c = i === null ? null : this.plan.columns[i];
    this.box.visible = !!c;
    if (c) {
      this.box.scale.set(W + 0.2, c.height + 0.2, W + 0.2);
      this.box.position.set(c.x, c.height / 2, c.z);
      this.flight.to([c.x, c.height / 2, c.z], [c.x + 4, c.height + 4, c.z + 8], 1);
    }
    this.onPick(c);
  }

  setMode(mode) {
    this.mode = mode;
    this.parts.forEach((b) => { b.mesh.visible = mode === "split"; });
    this.whole.mesh.visible = mode === "cogs";
  }

  /** Light up one place (by name), or all with null. */
  setPlace(name) {
    this.place = name;
    const lit = (r) => !name || (r.column.day.location_name || "Business") === name;
    [...this.parts, this.whole].forEach((b) => b.paint(lit, this.stage.dark));
    const row = this.plan.places.indexOf(name);
    if (row < 0) return this.home();
    const z = (row - (this.plan.places.length - 1) / 2) * this.plan.step.z, w = this.plan.size.w;
    this.flight.to([0, 2, z], [w * 0.15, 5 + w * 0.12, z + w * 0.5 + 5], 1.1);
  }

  spin(on) { this.stage.controls.autoRotate = on; }
}
