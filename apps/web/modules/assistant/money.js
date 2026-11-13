/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Assistant skills about money: who owes us, which bills to pay, how the month is going, which dishes earn the most.
import { cents, currency, thisMonth } from "./util.js";

export const owed = {
  id: "owed", title: "Who owes us", perm: ["billing", "manage_business"],
  words: ["owe", "owes", "owed", "debt", "receivable", "overdue", "unpaid", "late", "collect", "customer", "invoice"],
  examples: ["who owes us money", "which invoices are overdue"],
  answer: async (t, ctx) => {
    const [d, cur] = await Promise.all([ctx.api("/sales"), currency()]);
    const open = (d.invoices || []).filter((i) => i.balance > 0 && i.kind !== "credit" && i.number).sort((a, z) => (z.status === "overdue") - (a.status === "overdue") || z.balance - a.balance);
    return { text: open.length ? `Customers owe ${cur} ${cents(d.owed)}, of which ${cur} ${cents(d.overdue)} is overdue.` : "Nobody owes you anything. 🎉",
      kpis: [{ label: "Owed", value: `${cur} ${cents(d.owed)}`, href: "#/sales" }, { label: "Overdue", value: `${cur} ${cents(d.overdue)}`, tone: d.overdue ? "bad" : "good", href: "#/sales" },
        { label: "Received this month", value: `${cur} ${cents(d.received_month)}`, tone: "good" }],
      items: open.map((i) => ({ title: i.customer_name, sub: !i.number ? "draft - not sent yet" : `${i.number} · ${i.status === "overdue" ? `overdue since ${i.due}` : `due ${i.due}`}`,
        value: `${cur} ${cents(i.balance)}`, tone: i.status === "overdue" ? "bad" : "", href: `#/sales/invoice/${i.invoice_id}` })),
      chips: ["which bills do we need to pay", "how are we doing this month"] };
  },
};

export const bills = {
  id: "bills", title: "Bills to pay", perm: ["payables", "manage_business"],
  words: ["bill", "bills", "pay", "payable", "due", "approve", "supplier", "owe", "creditor"],
  examples: ["which bills do we need to pay", "bills waiting for approval"],
  answer: async (t, ctx) => {
    const [d, cur] = await Promise.all([ctx.api("/bills"), currency()]);
    const open = (d.bills || []).filter((b) => b.balance > 0 && b.state !== "void");
    return { text: open.length ? `${open.length} supplier bill${open.length === 1 ? "" : "s"} to pay; ${d.to_approve} waiting for approval.` : "No supplier bills are waiting to be paid.",
      kpis: [{ label: "Overdue", value: `${cur} ${cents(d.due.overdue)}`, tone: d.due.overdue ? "bad" : "good", href: "#/bills" },
        { label: "Due this week", value: `${cur} ${cents(d.due.this_week)}`, tone: d.due.this_week ? "warn" : "", href: "#/bills" }, { label: "To approve", value: d.to_approve, href: "#/bills" }],
      items: open.map((b) => ({ title: b.supplier_name, sub: `${b.supplier_ref} · due ${b.due}${b.state === "entered" ? " · needs approval" : ""}`, value: `${cur} ${cents(b.balance)}`,
        tone: b.overdue ? "bad" : "", href: `#/bills/${b.bill_id}` })),
      links: d.to_bill?.length ? [{ label: `${d.to_bill.length} received order(s) still to bill`, href: "#/bills" }] : [] };
  },
};

export const month = {
  id: "month", title: "How the month is going", perm: ["view_costs"],
  words: ["cogs", "cost", "costs", "profit", "sales", "revenue", "month", "doing", "food", "margin", "earn", "made", "performance"],
  examples: ["how are we doing this month", "what is our COGS this month", "profit this month"],
  answer: async (t, ctx) => {
    const [s, cur] = await Promise.all([ctx.api(`/costs/month?month=${thisMonth()}`), currency()]);
    const [lo, hi] = s.cogs_range || [25, 35], cogsTone = s.cogs_pct == null ? "" : s.cogs_pct > hi || s.cogs_pct < lo ? "bad" : "good";
    return { text: `This month: sales ${ctx.money(s.sales, cur)}, COGS ${ctx.num(s.cogs_pct)}% (target ${lo}-${hi}%)${s.net_profit != null ? `, net profit ${ctx.money(s.net_profit, cur)}` : ""}.`,
      kpis: [{ label: "Sales", value: ctx.money(s.sales, cur), href: "#/costs" }, { label: "COGS", value: `${ctx.num(s.cogs_pct)}%`, tone: cogsTone, href: "#/costs" },
        { label: "Net profit", value: s.net_profit == null ? "not yet" : ctx.money(s.net_profit, cur), tone: s.net_profit < 0 ? "bad" : "good", href: "#/costs" },
        { label: "Days outside target", value: s.days_out_of_range, tone: s.days_out_of_range ? "warn" : "good", href: "#/costs" }],
      items: s.missing?.length ? [{ title: "Missing costs", sub: s.missing.join(", "), tone: "warn", href: "#/setup" }] : [],
      chips: ["which dishes make the most profit", "who owes us money"] };
  },
};

export const best = {
  id: "best", title: "Most profitable dishes", perm: ["manage_business"],
  words: ["best", "top", "most", "profitable", "selling", "margin", "dish", "dishes", "product", "worst", "losing"],
  examples: ["which dishes make the most profit", "what is sold below cost"],
  answer: async (t, ctx) => {
    const [d, cur] = await Promise.all([ctx.api(`/money/margins?from=${thisMonth()}-01`), currency()]);
    const rows = d.products.filter((p) => p.item_id).slice(0, 6);
    return { text: rows.length ? `This month's invoiced sales, by profit (margin ${d.total.margin ?? "-"}% overall):` : "No invoiced sales this month yet.",
      items: rows.map((p) => ({ title: p.name, sub: `${p.qty} ${p.unit} sold · margin ${p.margin ?? "-"}%`, value: `${cur} ${cents(p.profit)}`, tone: p.profit < 0 ? "bad" : "good", href: "#/money/margins" })),
      links: d.below_cost.length ? [{ label: `Sold below cost: ${d.below_cost.join(", ")}`, href: "#/money/margins" }] : [] };
  },
};

export const MONEY = [owed, bills, month, best];
