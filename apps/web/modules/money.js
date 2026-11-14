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
import { prices } from "./money/prices.js";
import { quoteEditor } from "./money/quote-editor.js";
import { quote, quotes } from "./money/quotes.js";
import { report } from "./money/report.js";
import { statementPage } from "./money/statement.js";

const SELL = { auth: "staff", tenant: true, area: "money", group: "Money", perm: ["billing", "manage_business"] };
const PAY = { auth: "staff", tenant: true, area: "money", group: "Money", perm: ["payables", "manage_business"] };

export const routes = [
  { path: "/sales", feature: "sales", nav: "Invoices", key: "n", icon: "receipt", ...SELL, keywords: "customer receivable ar billing", render: sales },
  { path: "/sales/quotes", feature: "quotes", nav: "Quotations", icon: "send", ...SELL, keywords: "quote catering event order estimate", render: quotes },
  { path: "/sales/quotes/new", feature: "quotes", ...SELL, render: (el) => quoteEditor(el, "") },
  { path: "/sales/quotes/edit/:id", feature: "quotes", ...SELL, render: (el, { args }) => quoteEditor(el, args[0]) },
  { path: "/sales/quote/:id", feature: "quotes", ...SELL, render: (el, { args }) => quote(el, args[0]) },
  { path: "/sales/prices", feature: "sales", ...SELL, keywords: "price list customer price quantity break discount", render: prices },
  { path: "/sales/customers", feature: "sales", ...SELL, render: customers },
  { path: "/sales/customer/:id", feature: "sales", ...SELL, render: (el, { args }) => statementPage(el, args[0]) },
  { path: "/sales/new", feature: "sales", ...SELL, render: (el) => editor(el, "") },
  { path: "/sales/edit/:id", feature: "sales", ...SELL, render: (el, { args }) => editor(el, args[0]) },
  { path: "/sales/invoice/:id", feature: "sales", ...SELL, render: (el, { args }) => detail(el, args[0]) },
  { path: "/bills", feature: "purchasing", nav: "Supplier bills", key: "b", icon: "inbox", ...PAY, keywords: "payable ap supplier invoice", render: bills },
  { path: "/bills/new", feature: "purchasing", ...PAY, render: newBill },
  { path: "/bills/:id", feature: "purchasing", ...PAY, render: (el, { args }) => bill(el, args[0]) },
  { path: "/money/report", nav: "Money summary", icon: "chart", auth: "staff", tenant: true, area: "money", group: "Money", perm: "manage_business",
    keywords: "profit loss p&l gst vat tax month sales purchases", render: report },
  { path: "/money/margins", nav: "Profit by product", icon: "trend", auth: "staff", tenant: true, area: "money", group: "Money", perm: "manage_business",
    keywords: "margin gross profit product customer cost", render: margins },
];
