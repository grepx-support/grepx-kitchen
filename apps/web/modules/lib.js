/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Shared helpers for the kitchen screens: the business, the chosen location, item lines that are quick to edit on a phone.
import { api, esc, state } from "../../app.js";

let cached = null;
export async function biz(fresh = false) {
  if (!cached || fresh) cached = await api("/me/business");
  return cached;
}
export const resetBiz = () => { cached = null; };
export const has = (perm) => !!state.me && ((state.me.perms || []).includes(perm) || (state.me.perms || []).includes("*"));
export const on = (b, module) => (b.business?.modules || {})[module] !== false;
export const fmt = (n, d = 2) => (n === null || n === undefined || n === "") ? "–" : Number(n).toLocaleString(undefined, { maximumFractionDigits: d });
export const money = (b, n) => (n === null || n === undefined) ? "–" : `${b.business?.currency || ""} ${fmt(n, 2)}`;

const KEY = "kitchen.location";
export function remembered(locations, filter = () => true) {
  const list = locations.filter(filter);
  let id = null;
  try { id = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
  return (list.find((l) => l.id === id) || list[0] || {}).id || "";
}
export function remember(id) { try { localStorage.setItem(KEY, id); } catch (e) { /* ignore */ } }

export function picker(locations, selected, filter = () => true, name = "location") {
  return `<select name="${name}" data-pick>${locations.filter(filter).map((l) =>
    `<option value="${esc(l.id)}" ${l.id === selected ? "selected" : ""}>${esc(l.name)} · ${esc(l.kind)}${l.holding ? " (holding)" : ""}</option>`).join("")}</select>`;
}

// Editable lines: [{item_id, item_name, unit, qty, hint}] -> a table with one number box per line, a remove button, and an
// "add item" row. read(el) gives back [{item_id, qty}] with empty boxes left out.
export function lines(rows, items, { label = "Quantity", allowAdd = true, hint = "" } = {}) {
  const row = (r) => `<tr data-item="${esc(r.item_id)}"><td>${esc(r.item_name)}<div class="muted small">${esc(r.hint || "")}</div></td>
    <td style="width:120px"><input type="number" inputmode="decimal" step="any" min="0" value="${r.qty ?? ""}" aria-label="${esc(label)} ${esc(r.item_name)}"></td>
    <td class="muted" style="width:50px">${esc(r.unit || "")}</td><td style="width:44px"><button type="button" class="btn small" data-x aria-label="Remove ${esc(r.item_name)}">✕</button></td></tr>`;
  const left = Object.values(items).filter((i) => !rows.some((r) => r.item_id === i.id));
  return `<table class="lines"><tr><th>Item</th><th>${esc(label)}</th><th></th><th></th></tr>${rows.map(row).join("") || ""}</table>
    ${hint ? `<p class="muted">${esc(hint)}</p>` : ""}
    ${allowAdd && left.length ? `<div class="row"><div><label>Add an item</label><select data-add><option value="">Choose…</option>${left.map((i) =>
      `<option value="${esc(i.id)}">${esc(i.name)} (${esc(i.unit)})</option>`).join("")}</select></div></div>` : ""}`;
}
export function wireLines(el, items) {
  el.querySelectorAll("[data-x]").forEach((b) => b.onclick = () => b.closest("tr").remove());
  const add = el.querySelector("[data-add]");
  if (add) add.onchange = () => {
    const i = items[add.value]; if (!i) return;
    const t = el.querySelector("table.lines");
    t.insertAdjacentHTML("beforeend", `<tr data-item="${esc(i.id)}"><td>${esc(i.name)}</td><td><input type="number" inputmode="decimal" step="any" min="0" aria-label="Quantity ${esc(i.name)}"></td><td class="muted">${esc(i.unit)}</td><td><button type="button" class="btn small" data-x aria-label="Remove">✕</button></td></tr>`);
    t.querySelector("tr:last-child [data-x]").onclick = (e) => e.target.closest("tr").remove();
    add.querySelector(`option[value="${CSS.escape(i.id)}"]`)?.remove(); add.value = "";
    t.querySelector("tr:last-child input").focus();
  };
}
export function readLines(el, keepZero = false) {
  return [...el.querySelectorAll("table.lines tr[data-item]")].map((tr) => ({ item_id: tr.dataset.item, qty: tr.querySelector("input").value }))
    .filter((l) => l.qty !== "" && (keepZero || Number(l.qty) > 0)).map((l) => ({ ...l, qty: Number(l.qty) }));
}
export async function itemMap() {
  const s = await api("/stock").catch(() => null);
  return s;
}
