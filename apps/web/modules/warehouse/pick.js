/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Picking on the phone: lines in bin order, each says which lot (expiry) to take; tick it, then "Done - send".
import { api, run } from "/assets/app.js";
import { confirm, html, icon, pageHead, pill, progress } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { openPdf } from "../money/common.js";
import { fmt } from "../lib/format.js";

export async function pickScreen(el, id) {
  const p = await api(`/warehouse/picks/${id}`);
  const open = p.state === "open";
  const done = p.lines.filter((l) => l.picked > 0).length;
  el.style.setProperty("--area", area("floor"));
  el.innerHTML = String(html`${pageHead({ ...head("floor"), title: `Pick for ${p.to_name}`, subtitle: `from ${p.from_name} · by ${p.by_name}`,
      actions: html`${pill(p.state, open ? "warn" : p.state === "done" ? "good" : "")} <button class="btn small" data-pick-pdf>${icon("printer", { size: 15 })} PDF</button>` })}
    ${progress(done, p.lines.length, { label: "Picked" })}
    <div class="stack k-section">${p.lines.map((l) => html`<article class="card k-pickline ${l.picked > 0 ? "done" : ""}">
      <div><h3>${l.name}</h3><p class="muted">${fmt(l.qty)} ${l.unit}${l.short ? html` · <span class="bad">${fmt(l.short)} missing in stock</span>` : ""}</p>
        <div class="k-take">${l.lots.map((x) => html`<span>${icon("pin", { size: 14 })} <b>${x.bin_code || "no bin"}</b> ${fmt(x.qty)} ${x.expiry ? `· exp ${x.expiry}` : ""}</span>`)}</div></div>
      ${open ? html`<div class="k-pickctl"><input type="number" min="0" step="any" value="${l.picked || l.qty}" data-qty="${l.item_id}" aria-label="Picked ${l.name}">
        <button class="btn ${l.picked > 0 ? "" : "primary"}" data-pick="${l.item_id}">${icon("check", { size: 16 })} ${l.picked > 0 ? "Picked" : "Pick"}</button></div>`
        : html`<b>${fmt(l.picked)} ${l.unit}</b>`}</article>`)}</div>
    ${open ? html`<div class="k-nav"><button class="btn" data-cancel>Cancel list</button><button class="btn primary" data-done>${icon("send", { size: 16 })} Done - send</button></div>` : ""}`);
  const again = () => pickScreen(el, id);
  el.querySelector("[data-pick-pdf]").onclick = () => openPdf(`/pdf/pick/${id}`);
  el.querySelectorAll("[data-pick]").forEach((btn) => btn.onclick = async () => {
    const qty = el.querySelector(`[data-qty="${CSS.escape(btn.dataset.pick)}"]`).value;
    if (await run(() => api(`/warehouse/picks/${id}/pick`, { method: "POST", body: { item_id: btn.dataset.pick, qty } }))) again();
  });
  el.querySelector("[data-done]")?.addEventListener("click", async () => {
    if (await run(() => api(`/warehouse/picks/${id}/complete`, { method: "POST" }), "Sent - it's waiting for a delivery run")) location.hash = "#/runs";
  });
  el.querySelector("[data-cancel]")?.addEventListener("click", async () => {
    if (await confirm({ title: "Cancel this pick list?", ok: "Cancel list", danger: true }) && await run(() => api(`/warehouse/picks/${id}/cancel`, { method: "POST" }))) again();
  });
}
