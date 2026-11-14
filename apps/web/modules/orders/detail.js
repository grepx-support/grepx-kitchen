/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One purchase order: the text for WhatsApp, its lines, and change / copy / cancel / receive; everything about it
// (lines ordered against received, bills, timeline); previous / next order (buttons, or J / K).
import { api, run, toast } from "/assets/app.js";
import { Basket, confirm, html, icon, openDialog, pageHead, pill } from "/assets/kit/index.js";
import { head } from "../lib/areas.js";
import { biz, has } from "../lib/business.js";
import { money, stamp } from "../lib/format.js";
import { receive } from "./common.js";
import { openPdf } from "../money/common.js";
import { orderSummary } from "./summary.js";

const TONE = { saved: "warn", received: "good", cancelled: "" };

/** J / K (or the arrow buttons) go to the next / previous order while this page is shown. */
function stepKeys(el, o) {
  const keys = (e) => {
    if (!el.isConnected) return window.removeEventListener("keydown", keys);
    if (e.target.closest?.("input, textarea, select, [contenteditable]") || e.ctrlKey || e.metaKey || e.altKey) return;
    const to = { j: o.next_id, k: o.prev_id }[e.key];
    if (to) location.hash = `#/orders/${to}`;
  };
  window.addEventListener("keydown", keys);
}

export async function detail(el, id) {
  const [b, o] = await Promise.all([biz(), api(`/orders/${id}`)]);
  const open = o.state === "saved";
  const wa = o.supplier_phone ? `https://wa.me/${o.supplier_phone.replace(/\D/g, "")}?text=${encodeURIComponent(o.text)}` : "";
  el.innerHTML = String(html`${pageHead({ ...head("orders"), title: o.number, subtitle: `${o.supplier_name} · ${stamp(o.created_at)}`,
    actions: html`${pill(o.state, TONE[o.state])}<button class="btn small" data-po-pdf>${icon("printer", { size: 15 })} PDF</button><a class="btn small" href="#/orders">${icon("board", { size: 15 })} Board</a>
      <a class="btn small" href="#/orders/list">${icon("list", { size: 15 })} List</a>
      <a class="btn small ${o.prev_id ? "" : "disabled"}" href="${o.prev_id ? `#/orders/${o.prev_id}` : "javascript:void 0"}" title="Newer order (K)">‹ Newer</a>
      <a class="btn small ${o.next_id ? "" : "disabled"}" href="${o.next_id ? `#/orders/${o.next_id}` : "javascript:void 0"}" title="Older order (J)">Older ›</a>` })}
    <div class="grid two"><section class="card accent"><h2>${icon("send")} Message for the supplier</h2><pre>${o.text}</pre>
      ${(o.sent || []).map((x) => html`<p class="muted small">${icon("check", { size: 14 })} Sent by ${x.channels.join(", ")} · ${stamp(x.at)} · ${x.by}</p>`)}
      <div class="row">${open && has("orders") ? html`<button class="btn primary" data-send>${icon("send", { size: 15 })} Send to supplier…</button>` : ""}
        <button class="btn" data-copy>${icon("copy", { size: 15 })} Copy</button>
        ${wa ? html`<a class="btn" target="_blank" rel="noopener" href="${wa}">${icon("message", { size: 15 })} WhatsApp</a>` : ""}
        ${has("orders") ? html`<button class="btn" data-dup>${icon("copy", { size: 15 })} Copy to new order</button>` : ""}
        ${open && has("orders") ? html`<button class="btn danger" data-cancel>${icon("x", { size: 15 })} Cancel</button>` : ""}</div>
      ${o.value !== undefined ? html`<p class="muted">Value at current costs: <b>${money(b, o.value)}</b></p>` : ""}</section>
    ${open ? html`<section class="card accent"><h2>${icon("list")} Change the lines</h2><div class="slot"></div>
      <div class="row"><button class="btn primary" data-receive>${icon("inbox", { size: 15 })} Receive…</button>
        ${has("orders") ? html`<button class="btn" data-save>Save changes</button>` : ""}</div></section>` : ""}</div>
    <section class="card k-section"><h2>${icon("info")} Everything about this order</h2>${orderSummary(o, b)}</section>`);
  stepKeys(el, o);
  el.style.setProperty("--area", head("orders").area);
  const slot = el.querySelector(".slot");
  const basket = open ? new Basket({ label: "Qty", lines: o.lines.map((l) => ({ item_id: l.item_id, name: l.item_name, unit: l.unit, qty: l.qty })) }).mount(slot) : null;
  const again = () => detail(el, id);
  el.querySelector("[data-po-pdf]").onclick = () => openPdf(`/pdf/order/${o.po_id || o.id}`);
  el.querySelector("[data-copy]").onclick = async () => { try { await navigator.clipboard.writeText(o.text); toast("Copied - paste it into WhatsApp"); } catch (e) { toast("Select the text and copy it."); } };
  el.querySelector("[data-dup]")?.addEventListener("click", async () => { const n = await run(() => api(`/orders/${o.id}/copy`, { method: "POST" }), "New order saved"); if (n) location.hash = `#/orders/${n.po_id}`; });
  el.querySelector("[data-cancel]")?.addEventListener("click", async () => {
    if (await confirm({ title: `Cancel ${o.number}?`, ok: "Cancel order", cancel: "Keep it", danger: true }) && await run(() => api(`/orders/${o.id}/cancel`, { method: "POST" }), "Cancelled")) again();
  });
  el.querySelector("[data-send]")?.addEventListener("click", async () => {
    const form = document.createElement("div");
    form.innerHTML = String(html`<p class="muted">The order goes to ${o.supplier_name} on each channel ticked. Without a provider set up it is only written to the outbox.</p>
      ${[["email", "Email"], ["whatsapp", "WhatsApp"], ["sms", "SMS"]].map(([k, t], n) => html`<label class="check"><input type="checkbox" value="${k}" ${n < 2 ? "checked" : ""}> ${t}</label>`)}`);
    if (await openDialog({ title: `Send ${o.number}`, body: form, actions: [{ label: "Back", value: "" }, { label: "Send", value: "send", primary: true }] }) !== "send") return;
    const channels = [...form.querySelectorAll("input:checked")].map((i) => i.value);
    if (channels.length && await run(() => api(`/orders/${o.id}/send`, { method: "POST", body: { channels } }), "Sent")) again();
  });
  el.querySelector("[data-receive]")?.addEventListener("click", async () => { if (await receive({ ...o, lines: o.lines.map((l) => ({ ...l, qty: basket.lines(true).find((x) => x.item_id === l.item_id)?.qty ?? l.qty })) })) again(); });
  el.querySelector("[data-save]")?.addEventListener("click", async () => { if (await run(() => api(`/orders/${o.id}`, { method: "POST", body: { lines: basket.lines() } }), "Saved")) again(); });
}
