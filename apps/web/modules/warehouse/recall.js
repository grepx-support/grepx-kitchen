/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Recall: type or pick a lot code - see, as a tree, where every unit went (places, dishes it was cooked into, customers it
// was sold to, waste), what is still on the shelves to pull, and which customers to call. Print it for the inspector.
import { api } from "/assets/app.js";
import { empty, html, icon, kpiRow, pill } from "/assets/kit/index.js";
import { frame } from "./common.js";

const KIND = { sale: ["sold", "bad"], return: ["returned to supplier", ""], send_out: ["sent", "info"], transfer_out: ["moved", "info"], use: ["cooked with", "warn"], waste: ["thrown away", ""],
  adjust: ["corrected", ""], count: ["count", ""] };

function tree(r) {
  return html`<ol class="rc-tree">${r.lots.map((l) => html`<li style="--depth:${l.depth}" class="rc-node ${l.qty > 0 ? "open" : ""}">
    <div class="rc-card"><b>${l.item_name}</b> ${l.lot_code ? pill(`lot ${l.lot_code}`, "info") : ""} <span class="muted">${l.how === "start" ? "" : l.how} · ${l.place}</span>
      <div class="small">${l.qty > 0 ? pill(`${l.qty} ${l.unit} still here - pull it`, "bad") : pill("none left", "good")} received ${l.received}${l.supplier ? ` from ${l.supplier}` : ""}${l.expiry ? ` · use by ${l.expiry}` : ""}</div>
      ${(l.uses || []).length ? html`<ul class="rc-uses">${l.uses.map((u) => { const [t, tone] = KIND[u.kind] || [u.kind, ""];
        return html`<li>${pill(t, tone)} ${u.qty} ${l.unit} · ${u.date}${u.customer_name ? html` to <b>${u.customer_name}</b>` : ""}${u.invoice_number ? ` (${u.invoice_number})` : ""}${u.note && !u.customer_name ? ` · ${u.note}` : ""}</li>`; })}</ul>` : ""}</div></li>`)}</ol>`;
}

export async function recall(el, q, b, place) {
  const body = frame(el, "recall", b, place, "Recall: follow a lot everywhere it went");
  const { codes } = await api("/warehouse/lot-codes");
  body.innerHTML = String(html`<form class="card accent row" data-find><label class="grow">Lot code or lot id<input name="code" list="rc-codes" value="${q.code || ""}" required placeholder="e.g. B-2026-11-01"></label>
      <datalist id="rc-codes">${codes.map((c) => html`<option value="${c.code}">${c.item_name} · ${c.received}</option>`)}</datalist>
      <button class="btn primary">${icon("search", { size: 16 })} Trace</button>${q.code ? html`<button type="button" class="btn" data-print>${icon("download", { size: 16 })} Print</button>` : ""}</form><div data-out></div>`);
  body.querySelector("[data-find]").onsubmit = (e) => { e.preventDefault(); location.hash = `#/warehouse/recall?location=${place}&code=${encodeURIComponent(e.target.code.value.trim())}`; };
  body.querySelector("[data-print]")?.addEventListener("click", () => window.print());
  const out = body.querySelector("[data-out]");
  if (!q.code) { out.innerHTML = String(empty({ icon: "search", title: "Start from a lot", text: "Lot codes are typed when goods are received. Every move, dish and sale after that is followed." })); return; }
  const r = await api(`/warehouse/recall?code=${encodeURIComponent(q.code)}`).catch(() => null);
  if (!r) { out.innerHTML = String(empty({ icon: "alert", title: "No lot with that code", text: "Check the code on the delivery note or label." })); return; }
  out.innerHTML = String(html`${kpiRow([{ label: "Lots reached", value: r.totals.lots }, { label: "Still on shelves", value: r.totals.on_hand, tone: r.totals.on_hand ? "bad" : "good" },
      { label: "Customers to call", value: r.totals.customers, tone: r.totals.customers ? "warn" : "good" }, { label: "Sold", value: r.totals.sold }])}
    <div class="grid two"><section class="card k-section"><h2>${icon("alert")} Pull from the shelves</h2>${r.on_hand.length ? html`<ul class="rc-list">${r.on_hand.map((l) =>
        html`<li><b>${l.qty} ${l.unit} ${l.item_name}</b> at ${l.place}${l.bin_id ? ` · bin ${l.bin_id}` : ""}</li>`)}</ul>` : html`<p class="good">Nothing left in stock.</p>`}</section>
      <section class="card k-section"><h2>${icon("users")} Customers to call</h2>${r.customers.length ? html`<ul class="rc-list">${r.customers.map((c) =>
        html`<li>${c.customer_id ? html`<a href="#/sales/customers?open=${c.customer_id}"><b>${c.name}</b></a>` : html`<b>${c.name}</b>`} - ${c.qty}${c.invoices.length ? ` · ${c.invoices.join(", ")}` : ""}</li>`)}</ul>` : html`<p class="muted">Not sold to anyone.</p>`}</section></div>
    ${r.made_from.length ? html`<section class="card k-section"><h2>Made from</h2><ul class="rc-list">${r.made_from.map((l) => html`<li><a href="#/warehouse/recall?location=${place}&code=${l.lot_id}">${l.item_name}${l.lot_code ? ` lot ${l.lot_code}` : ""}</a> ${l.supplier ? `from ${l.supplier}` : ""}</li>`)}</ul></section>` : ""}
    <section class="card k-section"><h2>${icon("list")} Where it went</h2>${tree(r)}</section>`);
}
