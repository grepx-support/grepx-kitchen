/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One place's costs for one month, as lines grouped into staff, premises and running costs - every standard category
// ready to fill, your own categories added, a note per line, the total as you type. Shares of costs paid for several
// places show read-only (change them with "Share a cost").
import { html, openDialog } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { post } from "./common.js";

const row = (c, l = {}) => html`<div class="oh-line" data-cat="${c.category}" data-group="${c.group}"><span>${c.category}</span>
  <input type="number" min="0" step="0.01" name="amount" value="${l.amount ?? ""}" placeholder="0"><input name="note" value="${l.note || ""}" placeholder="note"></div>`;

export async function editCosts({ place, month, lines, categories, groups }) {
  const mine = Object.fromEntries(lines.filter((l) => !l.shared).map((l) => [l.category, l]));
  const cats = [...categories, ...lines.filter((l) => !l.shared && !categories.some((c) => c.category === l.category))];
  const box = document.createElement("form");
  box.className = "oh-edit";
  box.innerHTML = String(html`${Object.entries(groups).map(([g, label]) => html`<h3>${label} <span class="muted small" data-sum="${g}"></span></h3>
      <div data-group-box="${g}">${cats.filter((c) => c.group === g).map((c) => row(c, mine[c.category]))}</div>`)}
    ${lines.some((l) => l.shared) ? html`<h3>Shares of costs paid for several places</h3>${lines.filter((l) => l.shared).map((l) =>
      html`<div class="oh-line muted"><span>${l.category}</span><b>${fmt(l.amount)}</b><span>${l.note}</span></div>`)}` : ""}
    <div class="row oh-add"><input name="new_cat" placeholder="Add your own cost, e.g. Security guard"><select name="new_group">${Object.entries(groups).map(([g, l]) => html`<option value="${g}">${l}</option>`)}</select>
      <button type="button" class="btn small" data-add>Add</button></div><p class="oh-total">Total <b data-total>0</b></p>`);
  const sum = () => {
    let all = 0;
    for (const g of Object.keys(groups)) {
      const t = [...box.querySelectorAll(`[data-group-box="${g}"] [name=amount]`)].reduce((s, i) => s + Number(i.value || 0), 0);
      box.querySelector(`[data-sum="${g}"]`).textContent = fmt(t);
      all += t;
    }
    box.querySelector("[data-total]").textContent = fmt(all + lines.filter((l) => l.shared).reduce((s, l) => s + l.amount, 0));
  };
  box.addEventListener("input", sum);
  box.querySelector("[data-add]").onclick = () => {
    const name = box.new_cat.value.trim(), group = box.new_group.value;
    if (!name) return;
    box.querySelector(`[data-group-box="${group}"]`).insertAdjacentHTML("beforeend", String(row({ category: name, group })));
    box.new_cat.value = "";
  };
  sum();
  if (await openDialog({ title: `${place.name} - ${month}`, body: box, wide: true, actions: [{ label: "Cancel", value: "" }, { label: "Save", value: "ok", primary: true }] }) !== "ok") return false;
  const out = [...box.querySelectorAll(".oh-line[data-cat]")].map((r) => ({ category: r.dataset.cat, group: r.dataset.group,
    amount: r.querySelector("[name=amount]").value, note: r.querySelector("[name=note]").value }));
  return post("/setup/overheads", { location_id: place.id, month, lines: out }, "Costs saved");
}
