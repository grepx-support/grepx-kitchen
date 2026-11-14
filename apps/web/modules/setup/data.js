/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Import / export: each kind of record as a card - fill in the template, export what is there (Excel or CSV), or bring
// a file in. A file is first checked row by row (nothing saved, every problem shown with its row number); then the
// rows that pass are imported. Importing again updates what matches instead of adding it twice.
import { api, run } from "/assets/app.js";
import { html, icon, openDialog, pill } from "/assets/kit/index.js";
import { download } from "../lib/download.js";
import { asDataUrl, pickFile } from "../lib/files.js";

const ORDER = "Suppliers, then items, then recipes and opening stock - each needs the ones before it.";

const preview = (r) => html`<p>${pill(`${r.creates} new`, "good")} ${pill(`${r.updates} updated`, "info")} ${r.failed ? pill(`${r.failed} with problems`, "bad") : ""}</p>
  <div class="oh-scroll" style="max-height:50vh"><table class="m-view"><thead><tr><th>Row</th><th>Record</th><th>What happens</th></tr></thead><tbody>
  ${r.rows.map((x) => html`<tr class="${x.errors.length ? "bad" : ""}"><td>${x.rows.join(", ")}</td><td>${x.label}</td>
    <td>${x.errors.length ? html`${x.errors.map((e) => html`<div class="bad small">${e}</div>`)}` : x.action === "update" ? "updated" : "added"}</td></tr>`)}</tbody></table></div>`;

async function bring(kind, title) {
  const file = await pickFile(".xlsx,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
  if (!file) return;
  const body = { name: file.name, file: await asDataUrl(file) };
  const checked = await run(() => api(`/data/${kind}/check`, { method: "POST", body }));
  if (!checked) return;
  const go = await openDialog({ title: `${title}: ${file.name} checked`, body: preview(checked), wide: true,
    actions: [{ label: "Cancel", value: "" }, ...(checked.ok ? [{ label: `Import ${checked.ok} ${checked.failed ? "that pass" : ""}`, value: "go", primary: true }] : [])] });
  if (go !== "go") return;
  const done = await run(() => api(`/data/${kind}/import`, { method: "POST", body }), "Imported");
  if (done) await openDialog({ title: `${title} imported`, body: preview(done), wide: true, actions: [{ label: "OK", value: "", primary: true }] });
}

export default {
  id: "data", label: "Import / export", icon: "download",
  async render(el) {
    const d = await api("/data");
    el.innerHTML = String(html`<p class="muted">Bring your records in from Excel or CSV, or take them out. ${ORDER}</p>
      <div class="grid two">${d.kinds.map((x) => html`<section class="card" data-kind="${x.kind}" data-title="${x.title}"><h2>${x.title}</h2>
        <p class="muted small">${x.notes.join(" ")}</p>
        <details><summary class="small">Columns</summary><ul class="small">${x.columns.map((c) => html`<li><b>${c.heading}${c.required ? " *" : ""}</b> - ${c.help}${c.example ? ` (e.g. ${c.example})` : ""}</li>`)}</ul></details>
        <div class="row"><button class="btn primary small" data-in>${icon("upload", { size: 15 })} Import a file…</button>
          <button class="btn small" data-get="template" data-fmt="xlsx">Template</button>
          <button class="btn small" data-get="export" data-fmt="xlsx">${icon("download", { size: 15 })} Excel</button>
          <button class="btn small" data-get="export" data-fmt="csv">CSV</button></div></section>`)}</div>`);
    el.addEventListener("click", (e) => {
      const card = e.target.closest("[data-kind]");
      if (!card) return;
      const get = e.target.closest("[data-get]");
      if (get) download(`/data/${card.dataset.kind}/${get.dataset.get}?format=${get.dataset.fmt}`, `${card.dataset.kind}.${get.dataset.fmt}`);
      if (e.target.closest("[data-in]")) bring(card.dataset.kind, card.dataset.title);
    });
  },
};
