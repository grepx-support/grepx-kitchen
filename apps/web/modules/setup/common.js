/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What every setup tab uses: saving, a drag-to-reorder list that remembers its order on the server, simple forms.
import { api, run } from "/assets/app.js";
import { html, icon, SortableList } from "/assets/kit/index.js";

export const post = (path, body, done) => run(() => api(path, { method: "POST", body }), done);

/** A list the owner can drag into order: rows [{id, title, sub, tag, href, off}] */
export const sortList = (rows, empty = "Nothing yet.") => rows.length ? html`<ul class="k-sort">${rows.map((r) => html`<li data-id="${r.id}" class="${r.off ? "muted" : ""}">
    <button type="button" class="kit-grip" aria-label="Move ${r.title} (arrow keys)">${icon("grip", { size: 16 })}</button><span class="tag">${r.tag || ""}</span>
    <span class="who"><b>${r.title}</b><small>${r.sub || ""}</small></span>${r.href ? html`<a class="btn small" href="${r.href}">Edit</a>` : ""}</li>`)}</ul>`
  : html`<p class="muted">${empty}</p>`;

/** Make the .k-sort list in el draggable; every new order is saved as the business's listing order. */
export function wireSort(el, list) {
  const ul = el.querySelector(".k-sort");
  if (ul) new SortableList(ul, { onChange: (ids) => post("/setup/order", { list, ids }, "Order saved") });
}

/** Read a form into an object of strings (checkboxes: true / false). */
export function values(form) {
  const out = Object.fromEntries(new FormData(form));
  form.querySelectorAll("input[type=checkbox][name]").forEach((c) => { out[c.name] = c.checked; });
  return out;
}

export const option = (list, v) => list.map((x) => html`<option ${x === v ? "selected" : ""}>${x}</option>`);
