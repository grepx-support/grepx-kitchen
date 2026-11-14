/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The driver's phone: today's run, the next stop big, navigate, arrive, deliver with name + signature, or report a problem.
import { api, run } from "/assets/app.js";
import { empty, h, html, icon, openDialog, pageHead, pill, progress, SignaturePad } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { routeLink } from "./run.js";

const OPEN = (s) => s.state === "pending" || s.state === "arrived";

export async function driver(el) {
  const { runs } = await api("/runs/mine");
  el.style.setProperty("--area", area("driver"));
  const r = runs.find((x) => x.state === "on_road") || runs[0];
  if (!r) { el.innerHTML = String(empty({ icon: "truck", title: "No run for you right now", text: "When the warehouse plans your run it shows here." })); return; }
  const next = r.stops.find(OPEN);
  const done = r.stops.filter((s) => !OPEN(s)).length;
  el.innerHTML = String(html`${pageHead({ ...head("driver"), title: r.name, subtitle: `${r.stops.length} stop${r.stops.length === 1 ? "" : "s"}${r.vehicle ? ` · ${r.vehicle}` : ""}`, actions: pill(r.state.replace("_", " "), "warn") })}
    ${progress(done, r.stops.length, { label: "Stops done" })}
    ${r.state === "planned" ? html`<p class="k-section"><button class="btn primary" data-start>${icon("truck", { size: 16 })} Start my run</button></p>` : ""}
    ${next ? html`<section class="card accent k-next k-section"><p class="k-date">Next stop · ETA ${next.eta || "-"}</p><h2>${next.name}</h2>
      <p>${next.address || "no address on file"} · ${next.lines} lines</p>
      <div class="row">${next.address ? html`<a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(next.address)}">${icon("map", { size: 16 })} Navigate</a>` : ""}
        ${r.state === "on_road" && next.state === "pending" ? html`<button class="btn" data-arrive="${next.stop_id}">${icon("pin", { size: 16 })} I'm here</button>` : ""}
        ${r.state === "on_road" ? html`<button class="btn primary" data-deliver="${next.stop_id}">${icon("check", { size: 16 })} Delivered</button>
          <button class="btn danger" data-fail="${next.stop_id}">Problem</button>` : ""}</div></section>` : html`<section class="card k-done k-section">${icon("check", { size: 48 })}<h2>All stops done</h2></section>`}
    <section class="card k-section"><h2>The run</h2>${r.stops.map((s, n) => html`<div class="k-row"><b>${n + 1}</b><span>${s.name}</span>${pill(s.eta && OPEN(s) ? `ETA ${s.eta}` : s.state, s.state === "delivered" ? "good" : s.state === "failed" ? "bad" : "")}</div>`)}
      ${routeLink(r.stops) ? html`<p><a class="btn small" target="_blank" rel="noopener" href="${routeLink(r.stops)}">${icon("map", { size: 15 })} Whole route</a></p>` : ""}</section>`);
  const again = () => driver(el);
  const post = (path, body, msg) => run(() => api(`/runs/${r.id}${path}`, { method: "POST", body }), msg);
  el.querySelector("[data-start]")?.addEventListener("click", async () => { if (await post("/start", {}, "On the road")) again(); });
  el.querySelector("[data-arrive]")?.addEventListener("click", async (e) => { if (await post(`/stops/${e.currentTarget.dataset.arrive}/arrive`, {}, "Arrived")) again(); });
  el.querySelector("[data-deliver]")?.addEventListener("click", async (e) => { if (await proof(post, e.currentTarget.dataset.deliver)) again(); });
  el.querySelector("[data-fail]")?.addEventListener("click", async (e) => { if (await problem(post, e.currentTarget.dataset.fail)) again(); });
}

async function proof(post, stopId) {
  const box = h("div");
  box.innerHTML = '<label>Received by<input name="receiver" placeholder="Name of the person"></label><label>Note (optional)<input name="note"></label><p class="muted small">Signature</p>';
  const pad = new SignaturePad({ label: "Signature of the receiver" }).appendTo(box);
  box.append(Object.assign(h("p"), { className: "muted small", textContent: "Your signature (driver)" }));
  const mine = new SignaturePad({ label: "Signature of the driver" }).appendTo(box);
  const go = await openDialog({ title: "Proof of delivery", body: box, actions: [{ label: "Back", value: "" }, { label: "Delivered", value: "yes", primary: true }] });
  if (go !== "yes") return false;
  return post(`/stops/${stopId}/deliver`, { receiver: box.querySelector("[name=receiver]").value, note: box.querySelector("[name=note]").value, signature: pad.toDataURL(),
    driver_signature: mine.toDataURL() }, "Delivered - the delivery note has both signatures");
}

async function problem(post, stopId) {
  const box = h("div");
  box.innerHTML = '<label>What happened<select name="r"><option>Store closed</option><option>Refused the delivery</option><option>No access / no parking</option><option>Damaged on the way</option><option value="">Other…</option></select></label><label>Details<input name="d"></label>';
  const go = await openDialog({ title: "Could not deliver", body: box, actions: [{ label: "Back", value: "" }, { label: "Report", value: "yes", danger: true }] });
  if (go !== "yes") return false;
  const reason = [box.querySelector("[name=r]").value, box.querySelector("[name=d]").value].filter(Boolean).join(" - ");
  return post(`/stops/${stopId}/fail`, { reason }, "Reported - the trip goes back to waiting");
}
