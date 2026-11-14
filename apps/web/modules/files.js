/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The file library: every file attached anywhere in the business, as cards grouped by kind of record - search, filter,
// open, or jump to the record it belongs to.
import { api } from "/assets/app.js";
import { empty, html, icon, pageHead, pill } from "/assets/kit/index.js";
import { openAttachment } from "./lib/attachments.js";
import { area, head } from "./lib/areas.js";

const KIND = { bill: ["Bills", "#/bills/"], order: ["Purchase orders", "#/orders/"], invoice: ["Invoices", "#/sales/invoice/"], quote: ["Quotations", "#/sales/quote/"],
  item: ["Items", "#/setup?tab=items&edit="], supplier: ["Suppliers", "#/setup?tab=suppliers&edit="], employee: ["People", "#/team/person?id="] };
const kindOf = (ref) => ref.split(":")[0];

async function library(el, q) {
  const { files } = await api("/attachments");
  el.style.setProperty("--area", area("setup"));
  const kinds = [...new Set(files.map((f) => kindOf(f.ref)))];
  const pick = q.kind || "", text = (q.q || "").toLowerCase();
  const shown = files.filter((f) => (!pick || kindOf(f.ref) === pick) && (!text || f.name.toLowerCase().includes(text) || (f.note || "").toLowerCase().includes(text)));
  el.innerHTML = String(html`${pageHead({ ...head("setup"), title: "Files", subtitle: `${files.length} file${files.length === 1 ? "" : "s"} attached across the business` })}
    <div class="k-body"><div class="card row fl-bar"><input type="search" placeholder="Search file names" value="${q.q || ""}" data-q class="grow">
      <a class="btn small ${pick ? "" : "primary"}" href="#/files">All</a>${kinds.map((k) => html`<a class="btn small ${pick === k ? "primary" : ""}" href="#/files?kind=${k}">${(KIND[k] || [k])[0]}</a>`)}</div>
    ${shown.length ? html`<div class="at-grid fl-grid">${shown.map((f) => html`<div class="at-card" data-open="${f.id}">
        <div class="at-thumb">${pill(f.type.split("/").pop().slice(0, 6).toUpperCase(), "info")}</div><div class="at-name">${f.name}</div>
        <div class="at-meta muted">${String(f.at).slice(0, 10)} · ${f.by}</div>
        ${KIND[kindOf(f.ref)] ? html`<a class="small" href="${KIND[kindOf(f.ref)][1]}${f.ref.split(":")[1]}" data-go>${icon("arrow", { size: 12 })} ${KIND[kindOf(f.ref)][0].replace(/s$/, "")}</a>` : ""}</div>`)}</div>`
      : empty({ icon: "upload", title: "No files yet", text: "Drop files on a bill, order, invoice, quote, item, supplier or person - they all show up here." })}</div>`);
  const byId = Object.fromEntries(files.map((f) => [f.id, f]));
  el.querySelectorAll("[data-open]").forEach((c) => c.onclick = (e) => { if (!e.target.closest("[data-go]")) openAttachment(byId[c.dataset.open]); });
  el.querySelector("[data-q]").onchange = (e) => { location.hash = `#/files?${pick ? `kind=${pick}&` : ""}q=${encodeURIComponent(e.target.value)}`; };
}

export const routes = [
  { path: "/files", nav: "Files", icon: "upload", area: "setup", group: "Setup", auth: "staff", tenant: true, render: library,
    keywords: "files documents attachments pdf photos certificates library" },
];
