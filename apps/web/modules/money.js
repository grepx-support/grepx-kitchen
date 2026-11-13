/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Money in and out: customer invoices (what customers owe) and supplier bills (what you owe). See money/*.
import { bill, bills, newBill } from "./money/bills.js";
import { detail, editor } from "./money/invoice.js";
import { customers, sales } from "./money/sales.js";
import { margins } from "./money/margins.js";
import { report } from "./money/report.js";
import { statementPage } from "./money/statement.js";

const SELL = { auth: "staff", tenant: true, area: "money", group: "Money", perm: ["billing", "manage_business"] };
const PAY = { auth: "staff", tenant: true, area: "money", group: "Money", perm: ["payables", "manage_business"] };

export const routes = [
  { path: "/sales", nav: "Invoices", key: "n", icon: "receipt", ...SELL, keywords: "customer receivable ar billing", render: sales },
  { path: "/sales/customers", ...SELL, render: customers },
  { path: "/sales/customer/:id", ...SELL, render: (el, { args }) => statementPage(el, args[0]) },
  { path: "/sales/new", ...SELL, render: (el) => editor(el, "") },
  { path: "/sales/edit/:id", ...SELL, render: (el, { args }) => editor(el, args[0]) },
  { path: "/sales/invoice/:id", ...SELL, render: (el, { args }) => detail(el, args[0]) },
  { path: "/bills", nav: "Supplier bills", key: "b", icon: "inbox", ...PAY, keywords: "payable ap supplier invoice", render: bills },
  { path: "/bills/new", ...PAY, render: newBill },
  { path: "/bills/:id", ...PAY, render: (el, { args }) => bill(el, args[0]) },
  { path: "/money/report", nav: "Money summary", icon: "chart", auth: "staff", tenant: true, area: "money", group: "Money", perm: "manage_business",
    keywords: "profit loss p&l gst vat tax month sales purchases", render: report },
  { path: "/money/margins", nav: "Profit by product", icon: "trend", auth: "staff", tenant: true, area: "money", group: "Money", perm: "manage_business",
    keywords: "margin gross profit product customer cost", render: margins },
];
