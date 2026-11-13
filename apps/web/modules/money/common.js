/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the money pages share: amounts in cents shown as money, status colours, the page header, opening a PDF.
import { state, toast } from "/assets/app.js";
import { html, pageHead, pill, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { has } from "../lib/business.js";

/** Cents -> "AUD 1,234.50" (the services keep money in whole cents). */
export const cash = (cents, currency = "") => `${currency ? `${currency} ` : ""}${((cents || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const TONE = { draft: "", open: "info", "part paid": "warn", overdue: "bad", paid: "good", void: "", entered: "warn", approved: "info",
  matched: "good", check: "bad", no_order: "" };
export const badge = (word) => pill(word === "no_order" ? "no order" : word, TONE[word] ?? "");

export const canSell = () => has("billing") || has("manage_business");
export const canPay = () => has("payables") || has("manage_business");

const TABS = () => [canSell() && { id: "sales", label: "Invoices", icon: "receipt", href: "#/sales" },
  canSell() && { id: "customers", label: "Customers", icon: "users", href: "#/sales/customers" },
  canPay() && { id: "bills", label: "Supplier bills", icon: "inbox", href: "#/bills" },
  has("manage_business") && { id: "report", label: "Summary", icon: "chart", href: "#/money/report" },
  has("manage_business") && { id: "margins", label: "Profit", icon: "trend", href: "#/money/margins" }].filter(Boolean);

export function frame(el, current, title, subtitle, actions = "") {
  el.style.setProperty("--area", area("money"));
  el.innerHTML = String(html`${pageHead({ ...head("money"), title, subtitle, actions })}${tabs(TABS(), current)}<div class="k-body"></div>`);
  return el.querySelector(".k-body");
}

/** PDFs need the login token, so they are fetched and opened as a file, not linked. */
export async function openPdf(path) {
  const win = window.open("", "_blank");
  try {
    const res = await fetch(`/api/v1${path}`, { headers: { Authorization: `Bearer ${state.session?.token}` } });
    if (!res.ok) throw new Error("Could not make the PDF");
    const url = URL.createObjectURL(await res.blob());
    if (win) win.location = url; else location.href = url;
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) { win?.close(); toast(e.message); }
}
