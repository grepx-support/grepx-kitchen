/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One fund: its totals, each party's promise / paid / pending / share, where the money went, month by month, and
// every movement (newest first, reversible). Record a movement from the top.
import { api, run } from "/assets/app.js";
import { DataTable, html, icon, kpiRow, openDialog, pageHead, pill } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { KIND, cash, fundDialog } from "./common.js";

async function move(f, people) {
  const box = document.createElement("form");
  box.innerHTML = String(html`<div class="row"><label>What happened<select name="kind">${Object.entries(KIND).map(([k, [label]]) => html`<option value="${k}">${label}</option>`)}</select></label>
    <label>Amount (${f.currency})<input name="amount" type="number" min="0.01" step="any" required></label><label>Date<input name="date" type="date" value="${new Date().toISOString().slice(0, 10)}"></label></div>
    <div class="row"><label>Party<select name="party_id"><option value="">-</option>${people.map((p) => html`<option value="${p.party_id}">${p.name}</option>`)}</select></label>
    <label>Due by (promises)<input name="due" type="date"></label><label>Used for<input name="purpose" placeholder="e.g. Lower Parel outlet"></label></div>
    <div class="row"><label>Reference<input name="ref" placeholder="bank ref, cheque no."></label><label>Note<input name="note"></label></div>`);
  if (await openDialog({ title: `Record - ${f.name}`, body: box, actions: [{ label: "Cancel", value: "" }, { label: "Record", value: "ok", primary: true }] }) !== "ok") return null;
  return run(() => api(`/funds/${f.fund_id}/entries`, { method: "POST", body: Object.fromEntries(new FormData(box)) }), "Recorded");
}

export async function fundPage(el, q) {
  const d = await api(`/funds/${encodeURIComponent(q.id)}`);
  const f = d.fund, t = d.totals, c = (x) => cash(x, f.currency);
  const top = Math.max(1, ...d.months.map((m) => Math.max(m.in, m.out)));
  el.style.setProperty("--area", area("funds"));
  el.innerHTML = String(html`${pageHead({ ...head("funds"), title: f.name, subtitle: `${f.currency}${f.purpose ? ` · ${f.purpose}` : ""}${f.rate_pct ? ` · ${f.rate_pct}% a year` : ""}`,
    actions: html`<a class="btn" href="#/funds">All funds</a><button class="btn" data-edit>${icon("edit", { size: 15 })} Change</button><button class="btn primary" data-move>${icon("plus", { size: 15 })} Record</button>` })}
    ${kpiRow([{ label: "Promised", value: c(t.committed), icon: "clipboard", area: "#7c3aed" }, { label: "Brought in", value: c(t.received), icon: "inbox", area: "#16a34a" },
      { label: "Pending", value: c(t.pending), icon: "clock", area: t.pending ? "#f59e0b" : "#94a3b8" }, { label: "Put to use", value: c(t.allocated), icon: "store", area: "#0ea5e9" },
      { label: "Available", value: c(t.available), icon: "coin", area: area("funds") }, ...(f.kind === "loan" ? [{ label: "Still owed", value: c(t.owed), icon: "alert", area: "#e11d48" }] : [])])}
    <div class="fd-two"><section class="card"><h2>${icon("users")} Who put money in</h2><table class="kit-table"><thead><tr><th>Party</th><th class="num">Promised</th><th class="num">In</th>
        <th class="num">Pending</th><th class="num">Paid back</th><th class="num">Share</th></tr></thead><tbody>${d.parties.map((p) => html`<tr><td>${p.name}</td><td class="num">${c(p.committed)}</td>
        <td class="num">${c(p.received)}</td><td class="num ${p.pending ? "warn" : ""}">${c(p.pending)}</td><td class="num">${c(p.returned)}</td><td class="num"><b>${p.share_pct}%</b></td></tr>`)}</tbody></table>
        ${d.overdue.map((o) => html`<p class="bad small">${o.name}: ${c(o.missing)} was due ${o.due}</p>`)}</section>
      <section class="card"><h2>${icon("store")} Where it went</h2>${d.uses.map((u) => html`<div class="fd-use"><span>${u.purpose}</span><i><b style="width:${Math.round(u.amount / Math.max(1, t.allocated) * 100)}%"></b></i><span>${c(u.amount)}</span></div>`)}
        <h3>Month by month</h3><div class="fd-months">${d.months.map((m) => html`<div title="${m.month}: in ${c(m.in)}, out ${c(m.out)}"><i class="in" style="height:${m.in / top * 100}%"></i><i class="out" style="height:${Math.max(0, m.out) / top * 100}%"></i><span>${m.month.slice(2)}</span></div>`)}</div></section></div>
    <section class="card k-section"><h2>Every movement</h2><div class="t"></div></section>`);
  new DataTable({ rows: d.entries, columns: [
    { key: "date", label: "Date" }, { key: "kind", label: "What", render: (e) => html`<span class="fd-kind" style="--k:${KIND[e.kind][1]}">${KIND[e.kind][0]}</span>${e.reversed ? html` ${pill("reversed", "")}` : ""}` },
    { key: "amount", label: "Amount", render: (e) => html`<b class="${e.reversed ? "muted" : ""}">${c(e.amount)}</b>` }, { key: "party", label: "Party" },
    { key: "purpose", label: "Used for" }, { key: "ref", label: "Ref" }, { key: "by", label: "By" },
    { key: "x", label: "", render: (e) => html`${e.reversed ? "" : html`<button class="btn small" data-rev="${e.entry_id}">Reverse</button>`}` }] }).mount(el.querySelector(".t"));
  const again = () => fundPage(el, q);
  el.querySelector("[data-move]").onclick = async () => { if (await move(f, d.people)) again(); };
  el.querySelector("[data-edit]").onclick = async () => { if (await fundDialog(f)) again(); };
  el.querySelector(".t").addEventListener("click", async (e) => {
    const id = e.target.closest("[data-rev]")?.dataset.rev;
    if (id && await run(() => api(`/funds/entries/${id}/reverse`, { method: "POST", body: { reason: "reversed" } }), "Reversed")) again();
  });
}
