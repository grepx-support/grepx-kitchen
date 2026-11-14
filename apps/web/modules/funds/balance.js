/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The capital position as a balance sheet (assets = liabilities + equity, it always balances), per currency.
import { html, icon, pill } from "/assets/kit/index.js";
import { cash } from "./common.js";

const side = (title, rows, total, cur) => html`<div class="bs-side"><h3>${title}</h3>${rows.filter(([, v]) => v).map(([k, v]) =>
  html`<div class="bs-row"><span>${k}</span><span class="${v < 0 ? "bad" : ""}">${cash(v, cur)}</span></div>`)}<div class="bs-row bs-total"><span>Total</span><span>${cash(total, cur)}</span></div></div>`;

export const balanceSheet = (sheets) => html`${Object.entries(sheets).map(([cur, b]) => html`<section class="card bs"><h2>${icon("chart")} Balance sheet of the funds (${cur})
  ${b.balances ? pill("balances", "good") : pill("does not balance", "bad")}</h2><div class="bs-grid">${side("Assets", b.assets, b.assets_total, cur)}
  <div class="bs-side">${side("Liabilities", b.liabilities, b.liabilities_total, cur)}${side("Equity", b.equity, b.equity_total, cur)}</div></div></section>`)}`;
