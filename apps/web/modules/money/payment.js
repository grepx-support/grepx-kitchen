/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// "Record a payment" dialog (invoices and bills): amount (defaults to what is still owed), date, how, reference.
import { html, openDialog } from "/assets/kit/index.js";
import { today } from "../lib/format.js";
import { cash } from "./common.js";

const METHODS = [["bank", "Bank transfer"], ["paynow", "PayNow"], ["card", "Card"], ["cash", "Cash"], ["cheque", "Cheque"], ["other", "Other"]];

export async function askPayment(title, balance, currency) {
  const form = document.createElement("form");
  form.className = "m-pay";
  form.innerHTML = String(html`<p class="muted">Still owed: <b>${cash(balance, currency)}</b></p><div class="row">
    <label>Amount<input name="amount" type="number" step="0.01" min="0.01" value="${(balance / 100).toFixed(2)}" required></label>
    <label>Date<input name="date" type="date" value="${today()}"></label></div><div class="row">
    <label>How<select name="method">${METHODS.map(([v, t]) => html`<option value="${v}">${t}</option>`)}</select></label>
    <label>Reference<input name="reference" maxlength="60" placeholder="bank ref, cheque no."></label></div>`);
  if (await openDialog({ title, body: form, actions: [{ label: "Cancel", value: "" }, { label: "Record payment", value: "ok", primary: true }] }) !== "ok") return null;
  return Object.fromEntries(new FormData(form));
}
