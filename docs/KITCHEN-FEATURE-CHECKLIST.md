# Kitchen ERP - living feature checklist

The restaurant / central-kitchen part of the GrepX ERP master prompt, checked against what is built here.
A line is ✅ only when its rules, storage, permissions, checks and tests work (master prompt, part 14).

✅ built and tested · 🟡 partly built (what is missing is said) · ⬜ not built yet · 🔒 needs an account, key or a
decision from the business first · ➖ not part of a restaurant kitchen (the general ERP's job)

Next up is marked **NEXT** (in the order it will be built).

## 1. Business, places and people
| Feature | Status | Where / what is missing |
|---|---|---|
| Several businesses on one platform, each sees only its own data | ✅ | every row has `tenant_id`; BFF takes it from the login |
| Outlets, central kitchens, warehouses, vans | ✅ | Setup → Locations (kind, holds stock, address) |
| Currency, time zone, tax (GST) per business | ✅ | Setup → Business; invoices use the tax rate |
| Modules on / off per business | ✅ | BUS-03 |
| Branding: logo on documents | ✅ | Setup → Business → Logo (PNG kept with its clear background, media-service); printed on every PDF - invoices, bills, orders, payslips, reports; initials when there is none |
| Close / reopen a business (operator) | ✅ | Platform → Businesses |
| Roles per business, permissions ticked by the owner | ✅ | Setup → Roles |
| Profile photos, login, password | ✅ | |
| Two-step login (authenticator app codes, 10 one-time recovery codes; operator can switch it off for a lost phone) | ✅ | Profile → Sign-in & security; Platform → Staff |
| Sign in with Google, Microsoft (any or one company's accounts), or any OpenID Connect company login (Okta, Auth0, Keycloak, Zoho...) | ✅ | buttons on the login page once the operator saves the client id on Integrations |
| SAML sign-in, passkeys, sign-in by emailed code | ⬜ | |
| Audit trail: every change - who, when, what, done or refused and why; filters, details, CSV | ✅ | Setup → Audit trail |
| Login history | ⬜ | |

## 2. Menu, recipes and costing (F&B extension)
| Feature | Status | Where / what is missing |
|---|---|---|
| Items: ingredients, made products, supplies; unit, barcode, shelf life, sale price | ✅ | Setup → Items |
| Recipes (ingredients per batch, batch size) | ✅ | Setup → Recipes |
| Cost per portion from the recipe | ✅ | used by Profit by product |
| Recipe cards: method steps (tick as you go), station, prep / cook time, yield after trim, portion, plating, holding time; scale to any amount; cost per portion and margin; print | ✅ | Chef → Recipe book |
| Cost history per dish | ⬜ | |
| Menu engineering (stars / plough-horses / puzzles / dogs) | ⬜ | **NEXT (step 2)** |
| Allergens (the 14) and veg / egg / non-veg / vegan marks on ingredients; dishes take theirs from the recipe; allergen chart to print | ✅ | Setup → Items; Chef → Allergen chart |
| Several units per item (case of 12 = 12 each) | ⬜ | one unit per item today |

## 3. Kitchen production
| Feature | Status | Where / what is missing |
|---|---|---|
| Weekly production target from usage, safety %, event extra | ✅ | Kitchen screen |
| Record batches made; ingredients used come off stock | ✅ | Kitchen screen, Terminal |
| Kitchen terminal (big screen, timers) | ✅ | Terminal |
| Forecast per dish per outlet per day, most accurate method chosen; "use as targets" | ✅ | forecast-service; Kitchen → Forecast |
| Prep list for today by station (the week's target over the days left, in whole batches), made today, links to the card | ✅ | Chef → Prep list |
| Food safety (HACCP): fridge / freezer / hot-holding temperatures, cooking and cooling, delivery temperature, opening / closing / weekly checklists per place; out of range needs the action taken; still due today; log for inspectors (print, CSV); home widget | ✅ | Daily → Food safety (compliance-service, reusable) |

## 4. Buying (procure to pay)
| Feature | Status | Where / what is missing |
|---|---|---|
| Suppliers (contact, phone, email) | ✅ | Setup → Suppliers |
| Recommended orders per supplier from usage | ✅ | Orders → Recommended |
| Purchase orders: save, change, copy, cancel, send by email / WhatsApp / SMS with the order PDF attached | ✅ | Orders |
| Purchase order PDF | ✅ | order page → PDF |
| Orders list: stage tabs, search, supplier and date filters, prev / next, J / K keys; board cards open a side drawer | ✅ | Orders → Board, List |
| Order timeline (made, sent, received, billed, approved, paid) and ordered-against-received lines | ✅ | order page, drawer, list |
| Goods receipt: in full or changed, expiry, batch, bin | ✅ | Warehouse in |
| Supplier bills, three-way match, approval with note on mismatch, payments | ✅ | Supplier bills |
| Supplier price history (every price per item from their bills) and price-jump alerts: a rise of the owner's % (default 10) over that supplier's last price is flagged on the bill and sent to the owners | ✅ | Approvals → price rises; `/approvals/prices` (payables-service PRICES) |
| Purchase approval above an amount set by the owner: such an order can't be sent until approved; approval holds for the value approved; rejected with a note | ✅ | Setup → Business; Approvals (purchase-service APPROVE) |
| Supplier portal, bidding | 🔒 | F5 / F8: needs the business's sharing rules |

## 5. Stock and warehouse
| Feature | Status | Where / what is missing |
|---|---|---|
| Stock per location, every movement kept (who, when, before / after, cost) | ✅ | |
| Receive, send, transfer, adjust (with reason), waste (with reason) | ✅ | |
| Lots, expiry, first-expiry-first-out, bins and zones | ✅ | Warehouse floor |
| Pick lists in bin order | ✅ | |
| Pick list PDF (bin order, tick boxes, signatures) | ✅ | pick page → PDF |
| Min / max per item and place, alerts (out of stock, low, below zero, expiring, expired) sent to the owner by email / WhatsApp / SMS | ✅ | Inventory control; channels in Outbox → What goes out |
| Stock takes (blind), variance and its value | ✅ | |
| Count sheet PDF (to count on paper, blind) | ✅ | Closing → Count sheet; stock-take result PDF ⬜ |
| Valuation (item cost, lot cost), ABC, days of cover, waste by reason | ✅ | |
| 3D warehouse: racks, cartons, expiry, fill, pick routes, keys, snapshot | ✅ | |
| Barcode scanning | ✅ | camera scan in item pickers |

## 6. Delivery to outlets and customers
| Feature | Status | Where / what is missing |
|---|---|---|
| Delivery runs (driver, vehicle, stop order, ETA) | ✅ | Delivery runs |
| Driver phone screen, proof of delivery with the receiver's and the driver's signatures | ✅ | My deliveries |
| Delivery note PDF: goods, from / to, driver and vehicle; once handed over who received it and when, with the driver's and the receiver's signatures | ✅ | a run's stop → Delivery note; Deliveries board card → Delivery note |

## 7. Closing the day (end of day)
| Feature | Status | Where / what is missing |
|---|---|---|
| Closing: counts, sales by type, issues, one per day, review | ✅ | Closing |
| Closing report PDF with every detail (counts vs system, differences and their value, sales, issues, who, signatures) | ✅ | Home → Closings → PDF |
| Cash-up: float, cash counted, card / UPI totals, over / short | ⬜ | |

## 8. Selling and money
| Feature | Status | Where / what is missing |
|---|---|---|
| Catering / wholesale customers, invoices (gapless numbers), credit notes, payments | ✅ | Invoices |
| Invoice PDF, email to customer | ✅ | |
| Customer statement with ageing, print | ✅ | browser print |
| Customer statement as a real PDF | ⬜ | **NEXT (PDF round)** |
| Payment reminders (manual and automatic) | ✅ | |
| Monthly money summary, profit by product and customer | ✅ | Money |
| Daily cost of goods, labour, rent, other; COGS range flags; cost landscape in 3D | ✅ | Costs |
| Funds: partners' / investors' capital, owner's capital, loans, grants; promises with due dates, money in, money put to use (outlet, project), paid back, interest, fund costs; pending and overdue promises, available, loan balance, each party's share, month-by-month flow; reversing keeps history; amounts carry their currency (one per fund now, more later) | ✅ | Money → Funds (fund-service, reusable) |
| Funds - utilisation (spent of what was put to use, per use); plan per fund (expected EBITDA per use, start, ramp, horizon, discount, payout, hurdle) with payback month, ROI, IRR, NPV, money multiple, cash-back curve; actual EBITDA per outlet against plan; each investor's expected payout and return; balance sheet of the funds (assets = liabilities + equity) | ✅ | Funds → a fund → Plan & returns; Funds overview |
| Several currencies in one fund (conversion at a rate) | ✅ | Funds round (5) |
| Catering quotations: event (date, time, venue, guests), menu lines, valid for N days; sent by email with the PDF; the customer says yes → order (SO number), or no (reason kept); expired quotes must be sent again; the order becomes a draft invoice with the same lines; pipeline, win rate, events coming up | ✅ | Money → Quotations (billing-service: SAVE / SEND / ACCEPT / DECLINE / CANCEL_QUOTE, INVOICE_ORDER, QUOTES) |
| Full double-entry accounts (ledger, balance sheet) | ➖ | the general ERP's accounting module; the kitchen keeps sub-ledgers (AR, AP) |
| POS sales import (Square), delivery apps (Swiggy / Zomato / Uber Eats) | 🔒 | F1 / F9: need the partner accounts |

## 9. People and shifts
| Feature | Status | Where / what is missing |
|---|---|---|
| Employees across outlets: position, home outlet and others, pay basis (monthly / hourly), emergency contact, documents with expiry warnings, leaving | ✅ | People → Team (employee-service, reusable by any product) |
| Weekly roster per outlet: click to add, drag to move, presets, copy last week, publish, clash check across outlets, open shifts, hours and labour cost, 48-hour warning | ✅ | People → Roster (roster-service, reusable) |
| Clock in / out with a PIN on the terminal, late minutes, worked hours | ✅ | People → Clock in / out |
| Leave: types (annual, sick, casual, unpaid, own), yearly allowance pro-rated for new joiners, carry-over, balances, request / approve / cancel, month calendar, no rostering on approved leave | ✅ | People → Leave (leave-service, reusable) |
| Payroll: monthly run from salary or clocked hours, joiners / leavers pro-rated, unpaid leave, overtime, bonuses, advances, payslips (print); locking the month puts each outlet's labour cost into Costs | ✅ | People → Payroll (payroll-service, reusable) |
| Statutory rules per country as plug-ins - India (EPF, ESI, Professional Tax, TDS new regime), Australia (PAYG + Medicare, super), Singapore (CPF, SDL), Basic - every rate in one settings page | ✅ | People → Payroll → Country & rates |
| Payslip PDF; sent by email / WhatsApp / SMS with the PDF attached, once the month is locked (one person or everyone; who could not be reached is listed; each send kept) | ✅ | Payroll → Send payslips…, or a payslip → Send… (payroll-service SEND_PAYSLIP) |
| Staff see their own shifts and payslips; mobile app screens | ⬜ | at the end, with the mobile app |

## 10. Messages (email, WhatsApp, SMS)
| Feature | Status | Where / what is missing |
|---|---|---|
| Email (SMTP), WhatsApp (Twilio or Meta Cloud API), SMS (Twilio); test mode logs instead of sending | ✅ | notification-service |
| Operator connects providers, tests the connection, sends a test message; keys sealed | ✅ | Integrations page (platform admin) |
| Each business chooses which automatic messages go out, on which channels, in its own words | ✅ | Outbox → What goes out |
| Failed sends tried again by themselves (5 min, 30 min, 2 h), "Try again now", tries shown | ✅ | Outbox → Sent |
| Files attached to messages (PDFs): email attachment; WhatsApp document (Meta: uploaded; Twilio: a link that works 14 days) | ✅ | `notify(..., attachments=)`; links: grepx-bff `shared_files` |
| Delivery receipts from the provider (delivered / read) | 🔒 | needs the provider's webhook address on the live server |

## 11. Experience
| Feature | Status | Where / what is missing |
|---|---|---|
| Ctrl+K search over pages, actions and records; G + letter; ? for keys | ✅ | |
| Pinned pages (star), Alt+1-9, folding menu groups | ✅ | |
| Dark and light theme, phone layouts | ✅ | |
| Dense full-width layout; charts expand and click through to their data; drag and drop with gap and soft landing | ✅ | every page |
| Sortable, paged tables (25 / 50 / 100 / all) that scroll inside; CSV download where it matters | 🟡 | paging and sorting everywhere; CSV on the money summary only - more with the import / export round |
| Saved filters per table | ⬜ | |
| Activity timeline on records | 🟡 | orders done; deliveries and invoices next |
| Approvals inbox: big orders, bills to approve (mismatches and price jumps first), leave requests, price rises - each only for who may decide it | ✅ | Approvals (G A) |
| Several languages | ⬜ | English only |
| Assistant: ask in your own words (stock, expiry, how much of X, orders, what to order, who owes, bills, month, best dishes, forecast, cooking, deliveries, open a page); cached answers; permissions respected | ✅ | chat button on every page, Ctrl+J |
| Assistant backed by an AI model (free-form questions) | 🔒 | needs an AI key and the owner's consent; the assistant has the slot for it |

## How each feature is built
Each service owns its tables; business rules are plain tested functions in `domain/`; one module per action in
`routes/`; small classes (Strategy for interchangeable methods, Template Method for documents and reports);
the BFF only joins and checks access; the web is split into small modules. Nothing is marked ✅ before its tests pass.

## Funds - the full model (round 5)

| Feature | Status | Where |
|---|---|---|
| Money given to a use against its real spending (a use named like a place: that place's ingredients, labour, rent, other costs since it got money), left / overspent, monthly burn, by category | ✅ | Funds; a fund → Forecast & advice |
| Cash forecast 12 months, three cases (expected / best with the plan's earnings / worst: overdue promises never come, the rest late), runway | ✅ | Funds; a fund → Forecast & advice |
| Suggestions: chase overdue promises, runway short, use overspent, behind plan, repay a dear loan early, idle cash | ✅ | Funds; a fund → Forecast & advice |
| Promises board: drag a promise to "Paid in" to record the money | ✅ | Funds |
| Drag a fund onto a place to put money to it; drag fund cards to reorder | ✅ | Funds |
| Balance sheet as of any date, every line opens to what is behind it (per fund, use, lender, partner); checks it balances | ✅ | Funds |
| Several currencies: money in another currency converted at its rate, the original kept; funds in another currency counted in the business currency at their rate | ✅ | Record; New fund / Change |
| Investor statement PDF per party; sent by email / WhatsApp with the PDF attached (each send kept) | ✅ | a fund → Who put money in → printer / send icons |
| Every movement as CSV | ✅ | a fund → Every movement → CSV |

## Monthly costs in full (round 5c)

| Feature | Status | Where |
|---|---|---|
| Costs as lines per place and month: 21 standard categories (salaries, overtime, staff meals, benefits, rent, service charge, property tax, electricity, gas, water, internet, delivery-app commission, card / UPI fees, marketing, repairs, cleaning, licences, insurance, software, accounting, fuel) plus your own, in three groups (staff / premises / running costs), a note each | ✅ | Setup → Monthly costs → click a cell |
| Six months side by side per place with the change on the month before; totals per month; this month by cost | ✅ | Setup → Monthly costs |
| Share a cost paid once for several places: equally, by sales, or by weights | ✅ | Setup → Monthly costs → Share a cost |
| Start a month from the month before | ✅ | Setup → Monthly costs → Copy |
| The Costs page shows the month's costs line by line | ✅ | Costs |

## Bulk import / export (round 6)

| Feature | Status | Where |
|---|---|---|
| Import from Excel (.xlsx) or CSV: suppliers, items, recipes (one row per ingredient), opening stock (per place), employees | ✅ | Setup → Import / export |
| Every row checked first (nothing saved), problems shown with their row numbers; then the rows that pass are imported through the owning services | ✅ | Setup → Import / export → Import a file… |
| Importing again updates what matches (by name, employees by email) instead of adding twice | ✅ | |
| Templates to fill in (with a "How to fill it in" sheet) and everything exported as Excel or CSV | ✅ | Setup → Import / export |

## Features, pictures (round 7)

| Feature | Status | Where |
|---|---|---|
| Setup → Features: 19 features in six groups, each explained in a line and switched on / off for the business; what is off leaves the menu and its API refuses (MODULE_OFF); data is kept | ✅ | Setup → Features |
| Item pictures: on the item list, the item's edit page and the recipe card | ✅ | Setup → Items → Edit → Picture |
| Every list row and board card opens what it is about | ✅ | everywhere (tables inside other screens still to go) |

## Compared with Unleashed (inventory software) - what we have and what is next

Grouped as Unleashed groups its features. ✅ we have it · 🟡 partly · ⬜ not yet (with the service it belongs in).

| Unleashed feature | Us | Notes / where it goes |
|---|---|---|
| **Inventory** | | |
| Real-time stock across places, transfers | ✅ | stock-service |
| Inventory counts (full / partial), reconcile | ✅ | closing counts, count sheets, stock adjust; posting to accounting ⬜ (with an accounting link) |
| Multi-warehouse | ✅ | places of every kind |
| Barcode scanning (receive, pick, count) | ✅ | warehouse screens |
| Batch tracking with expiry, recalls | 🟡 | lots and expiry ✅ (warehouse-service); recall report "which customers got lot X" ⬜ |
| Serial numbers | ⬜ | rarely needed for food; equipment register (asset-service, generic) if wanted |
| Replenishment (min / max per item) and reorder prompts | ✅ | par levels, suggested orders |
| Forecasting | ✅ | forecast-service |
| Inventory optimisation (dead / over stock) | 🟡 | slow movers report ✅; over-stock alert ⬜ (inventory-service) |
| **Orders (selling)** | | |
| Sales quotes → orders | ✅ | catering quotations |
| Sales orders from all channels, invoicing | 🟡 | invoices ✅; standing / online orders from outlets and B2B customers ⬜ (order-service, product) |
| Freight and charges on quotes / orders | ✅ | billing-service charge lines (delivery, freight, service) totalled apart; "Add a charge" on invoices and quotes |
| Customer pricing (fixed price or % per customer) | ✅ | billing-service customer pricing; Money → Price lists; lines fill the customer's price |
| Quantity discounts (price breaks) | ✅ | billing-service price_breaks; repriced as the quantity changes |
| **Purchasing** | | |
| Suppliers with prices, currencies, lead times, performance | 🟡 | suppliers, price history ✅; lead time, supplier currency, on-time rate ⬜ (item- / purchase-service) |
| Landed cost (duty, freight, labour on a purchase) | ⬜ | purchase-service: costs spread over the lines into the unit cost |
| Recost a purchase when the bill arrives | 🟡 | bill matched to the order with price differences ✅; updating stock value ⬜ |
| Supplier returns | ⬜ | purchase-service RETURN (stock out, credit expected) |
| Partial receipts against an order | ✅ | |
| **Production** | | |
| Bill of materials (recipes) drawing down stock | ✅ | recipes, kitchen production |
| Assemblies / what can be made from stock | 🟡 | production plan ✅; "can make N from stock now" ⬜ (planning-service) |
| Disassembly (whole chicken → cuts, cost split) | ⬜ | planning-service BREAK_DOWN with yields |
| Kits / bundles (combo meals) | ⬜ | item-service: a sold item made of others, stock taken on sale |
| Kanban planner | ✅ | order, delivery and production boards |
| **General** | | |
| Reports, dashboards | ✅ | costs, money, stock, dashboards |
| Pick, pack, dispatch | ✅ | pick lists, delivery runs, delivery notes |
| File library on products, customers, suppliers, transactions | 🟡 | item pictures, employee documents ✅; attachments on any record ⬜ (media-service, generic) |
| Open API with keys | ⬜ | grepx-bff API keys per business (generic) |
| Data import / export | ✅ | round 6 |
| **Add-ons** | | |
| B2B ordering store (customers order online at their prices) | ⬜ | product app on billing price lists |
| CRM | 🟡 | lead-service ✅ (leads); activity history per customer ⬜ |
| Accounting (Xero / QuickBooks) | ⬜ | integration-service: invoices, bills, payments out |
| E-commerce / delivery apps (Shopify, Grab, Swiggy...) | ⬜ | integration-service: orders in, stock out |

**Suggested next, in order:** ~~(1) customer price lists, quantity breaks and charge lines~~ done; (2) landed cost and recosting on the bill; (3) supplier returns; (4) disassembly and combo items; (5) attachments on any record; (6) recall report by lot; (7) API keys; (8) accounting link.

