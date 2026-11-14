/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Funds overview: how much money was brought in, how much is still promised (and overdue), where it was put, what is
// available, loans owed - across every fund; one card per fund with its progress to target.
import { api } from "/assets/app.js";
import { empty, html, icon, kpiRow, pageHead } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { FUND_KIND, cash, fundDialog, partyDialog } from "./common.js";

const card = (f) => html`<a class="card fd-card fd-${f.kind}" href="#/funds/fund?id=${f.fund_id}"><header><b>${f.name}</b><span class="muted small">${FUND_KIND[f.kind]}</span></header>
  <div class="fd-big">${cash(f.received, f.currency)}<span class="muted small"> in</span></div>
  ${f.target_progress != null ? html`<div class="fd-bar"><i style="width:${Math.min(100, f.target_progress)}%"></i></div><p class="muted small">${f.target_progress}% of ${cash(f.target, f.currency)} target</p>` : ""}
  <dl class="fd-mini"><dt>Promised, not in yet</dt><dd class="${f.pending ? "warn" : ""}">${cash(f.pending, f.currency)}</dd><dt>Put to use</dt><dd>${cash(f.allocated, f.currency)}</dd>
    <dt>Available</dt><dd><b>${cash(f.available, f.currency)}</b></dd>${f.kind === "loan" ? html`<dt>Still owed</dt><dd class="bad">${cash(f.owed, f.currency)}</dd>` : ""}</dl></a>`;

export async function fundsPage(el) {
  const o = await api("/funds");
  const [cur, t] = Object.entries(o.totals)[0] || [o.currency, {}];
  el.style.setProperty("--area", area("funds"));
  el.innerHTML = String(html`${pageHead({ ...head("funds"), title: "Funds", subtitle: "Money brought in, promised, put to use and paid back - across every fund.",
    actions: html`<button class="btn" data-party>${icon("users", { size: 15 })} Add a party</button><button class="btn primary" data-fund>${icon("plus", { size: 15 })} New fund</button>` })}
    ${kpiRow([{ label: "Brought in", value: cash(t.received, cur), icon: "inbox", area: "#16a34a" },
      { label: "Promised, not in yet", value: cash(t.pending, cur), icon: "clock", area: "#7c3aed", note: o.overdue.length ? `${o.overdue.length} overdue` : "", tone: o.overdue.length ? "bad" : "" },
      { label: "Put to use", value: cash(t.allocated, cur), icon: "store", area: "#0ea5e9" }, { label: "Available", value: cash(t.available, cur), icon: "coin", area: area("funds") },
      { label: "Paid back", value: cash(t.returned, cur), icon: "outbox", area: "#f59e0b" }])}
    ${Object.keys(o.totals).length > 1 ? html`<p class="muted small">Totals per currency: ${Object.entries(o.totals).map(([c, x]) => `${c} ${cash(x.received, c)} in`).join(" · ")}</p>` : ""}
    ${o.overdue.length ? html`<section class="card fd-late"><h2>${icon("alert")} Overdue promises</h2>${o.overdue.map((x) => html`<div><b>${x.name}</b> was due ${x.due}
      - <span class="bad">${cash(x.missing, cur)} not in yet</span></div>`)}</section>` : ""}
    ${o.funds.length ? html`<div class="fd-grid">${o.funds.map(card)}</div>` : empty({ icon: "coin", title: "No funds yet", text: "Add a fund: partners' capital, an investor round, a bank loan or a grant." })}`);
  el.querySelector("[data-fund]").onclick = async () => { if (await fundDialog()) fundsPage(el); };
  el.querySelector("[data-party]").onclick = async () => { if (await partyDialog()) fundsPage(el); };
}
