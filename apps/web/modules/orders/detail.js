/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One purchase order: the text for WhatsApp, its lines, and change / copy / cancel / receive.
import { api, esc, run, toast } from "/assets/app.js";
import { Basket, confirm, html, icon, pageHead, pill } from "/assets/kit/index.js";
import { head } from "../lib/areas.js";
import { biz, has } from "../lib/business.js";
import { fmt, money, stamp } from "../lib/format.js";
import { receive } from "./common.js";

const TONE = { saved: "warn", received: "good", cancelled: "" };

export async function detail(el, id) {
  const [b, o] = await Promise.all([biz(), api(`/orders/${id}`)]);
  const open = o.state === "saved";
  const wa = o.supplier_phone ? `https://wa.me/${o.supplier_phone.replace(/\D/g, "")}?text=${encodeURIComponent(o.text)}` : "";
  el.innerHTML = String(html`${pageHead({ ...head("orders"), title: o.number, subtitle: `${o.supplier_name} · ${stamp(o.created_at)}`,
    actions: html`${pill(o.state, TONE[o.state])}<a class="btn small" href="#/orders">${icon("board", { size: 15 })} Board</a>` })}
    <div class="grid two"><section class="card accent"><h2>${icon("send")} Message for the supplier</h2><pre>${o.text}</pre>
      <div class="row"><button class="btn" data-copy>${icon("copy", { size: 15 })} Copy</button>
        ${wa ? html`<a class="btn" target="_blank" rel="noopener" href="${wa}">${icon("message", { size: 15 })} WhatsApp</a>` : ""}
        ${has("orders") ? html`<button class="btn" data-dup>${icon("copy", { size: 15 })} Copy to new order</button>` : ""}
        ${open && has("orders") ? html`<button class="btn danger" data-cancel>${icon("x", { size: 15 })} Cancel</button>` : ""}</div>
      ${o.value !== undefined ? html`<p class="muted">Value at current costs: <b>${money(b, o.value)}</b></p>` : ""}</section>
    <section class="card accent"><h2>${icon("list")} ${open ? "Lines" : "Received"}</h2><div class="slot"></div>
      ${open ? html`<div class="row"><button class="btn primary" data-receive>${icon("inbox", { size: 15 })} Receive…</button>
        ${has("orders") ? html`<button class="btn" data-save>Save changes</button>` : ""}</div>` : ""}</section></div>`);
  el.style.setProperty("--area", head("orders").area);
  const slot = el.querySelector(".slot");
  const basket = open ? new Basket({ label: "Qty", lines: o.lines.map((l) => ({ item_id: l.item_id, name: l.item_name, unit: l.unit, qty: l.qty })) }).mount(slot) : null;
  if (!open) slot.innerHTML = (o.received || o.lines).map((l) => `<div class="item"><b>${fmt(l.qty)}</b> × ${esc(o.lines.find((x) => x.item_id === l.item_id)?.item_name || l.item_id)}</div>`).join("");
  const again = () => detail(el, id);
  el.querySelector("[data-copy]").onclick = async () => { try { await navigator.clipboard.writeText(o.text); toast("Copied - paste it into WhatsApp"); } catch (e) { toast("Select the text and copy it."); } };
  el.querySelector("[data-dup]")?.addEventListener("click", async () => { const n = await run(() => api(`/orders/${o.id}/copy`, { method: "POST" }), "New order saved"); if (n) location.hash = `#/orders/${n.po_id}`; });
  el.querySelector("[data-cancel]")?.addEventListener("click", async () => {
    if (await confirm({ title: `Cancel ${o.number}?`, ok: "Cancel order", cancel: "Keep it", danger: true }) && await run(() => api(`/orders/${o.id}/cancel`, { method: "POST" }), "Cancelled")) again();
  });
  el.querySelector("[data-receive]")?.addEventListener("click", async () => { if (await receive({ ...o, lines: o.lines.map((l) => ({ ...l, qty: basket.lines(true).find((x) => x.item_id === l.item_id)?.qty ?? l.qty })) })) again(); });
  el.querySelector("[data-save]")?.addEventListener("click", async () => { if (await run(() => api(`/orders/${o.id}`, { method: "POST", body: { lines: basket.lines() } }), "Saved")) again(); });
}
