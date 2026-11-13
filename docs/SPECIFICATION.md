<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->

# Kitchen Stock & Costing - specification (from HFT BRD v0.2)

Where each requirement of the BRD is built. Services are in `product-services/kitchen/`, the API in
`apps/kitchen-bff/src/routers/`, screens in `apps/web/modules/` and `apps/mobile/lib/screens/`.

## Open questions - the answers used (BRD section 14, all "proposed answers")

| # | Used | Where |
|---|---|---|
| Q1 | Roles: owner (administrator), warehouse, kitchen, store/truck (closing), delivery - as per-business staff roles | catalog/access.yaml |
| Q2 | GrepX sets up each business (operator page **Businesses**); no self sign-up | kitchen-bff `platform.py` |
| Q3 | Locations, items, suppliers, costs and current stock are entered (or receipts recorded) in the new system | Setup + Warehouse in |
| Q4 | Finished goods go through the holding place: kitchen → transfer to warehouse → warehouse out | stock SEND requires a holding source |
| Q5 | Supplier deliveries arrive at a holding place; a kitchen storage area can be one (location "holds stock") | purchase-service, business-service |
| Q6 | A closing count replaces system stock; the difference and staff name are kept; the owner reviews differences | stock COUNT, `/closing/history` |
| Q7 | Batch output is entered and editable per product | Setup → Recipes |
| Q8 | The owner defines the sales types for closing | business settings `sales_types` |
| Q9 | Costing average = (ingredient cost + labour + rent + other) / sales | costing domain |
| Q10 | Labour, rent, other: monthly per location, spread equally over the days of the month | costing domain, Setup → Monthly costs |
| Q11 | Saves are single requests (typically well under 3 s); measured live on the ops screen | `/ops/` |
| Q12 | Event weeks: the owner adds an extra quantity for the week | planning SET_TARGET `extra` |
| Q13 | Internet connection required | - |
| Q14 | Everything in the MVP was built; nothing cut | - |

## Rules (section 7)

| Rule | Built as |
|---|---|
| D1 / R1 | warehouse out (SEND) must start at a holding location; supplier orders arrive at one |
| D2 / BUS-04 | any location can "hold stock"; a kitchen can be the holding place |
| D3 / R2 | TRANSFER between any two locations (one record moves out and in) |
| D4 / ACC-03 | per-business roles; the owner ticks which roles may adjust stock |
| D5 / BUS-03 | modules on/off per business; the API refuses switched-off modules (MODULE_OFF) and the apps hide them |
| D6 | PRODUCE only at a kitchen, only finished products |
| D7 | sales are typed at closing |
| R3 | ADJUST sets the right quantity and needs a reason |
| R4 | warehouse out suggestion = daily usage at the location × days of cover − stock there |
| R5 / KIT-03 | target = weekly usage (last 1-3 weeks) × (1 + safety %) + event extra − stock on hand anywhere |
| R6 / ORD-02 | reorder = weekly usage × (1 + safety %) − stock in the business − already on order; a person decides |
| R7 | COGS % = cost of what was consumed in the count period / sales in the same period (see costing below) |
| R8 | costing average (Q9) |
| R9 / COS-07 | each business sets its COGS range; days outside it are flagged |
| R10 / CLS-07 | each location: count every 1, 3 or 7 days |

**Usage** (planning): ingredients recorded as used + what disappeared between counts (a count below system stock).
Adjustments are corrections, not usage. Today is not counted (not a full day). A business with less history than the
window is averaged over the days it has; with none, quantities are typed by hand (KIT-10, ORD-10).

**COGS** (costing): consumed = (system stock − counted) at the closing, valued at the item cost when it moved, plus
ingredients recorded as used at a location that is not a kitchen. A kitchen's recorded use turns ingredients into
finished goods whose cost counts where they are consumed, so it is not counted twice. Items with no cost are listed as
"item cost" missing.

## Requirements (section 8)

| ID | Where |
|---|---|
| BUS-01, BUS-05 | business-service (tenant), BFF `Kitchen` (tenant from the token on every command and read); tested with two businesses |
| BUS-02 | Setup tabs: locations, items, suppliers, users |
| BUS-03 | business `modules`, BFF `allow(module=…)`, web/mobile hide them |
| BUS-06 | business currency + time zone; dates of movements and closings use the business time zone |
| ACC-01..03 | Setup → Users (one role each), Roles (tick permissions per role) |
| ACC-04 / QR-01 | phone-first web screens + Flutter app |
| ACC-05 / INV-10 / QR-06 | every stock movement: user, time, kind, quantity before/after, note, unit cost; append-only |
| KIT-01, KIT-02 | Setup → Items (finished), Recipes |
| KIT-03..05, KIT-10 | Kitchen screen: target, batches, ingredients to buy; owner can type a target or event extra |
| KIT-06..09 | Kitchen screen: record production (adds finished goods), ingredients used (reduces stock) |
| INV-01 | Stock screen |
| INV-02..04 | Warehouse out: suggestion per location (days of cover from the location), accept / change / remove lines |
| INV-05 | Warehouse in: what the holding place needs for the week |
| INV-06..09 | receive, send, transfer, adjust (only roles the owner chose) |
| INV-11 | closing review and history show counted vs system |
| ORD-01..10 | Orders: recommendation per supplier with previous and large-change flag; save, add items, change, copy, cancel, receive in full or changed; copy text / WhatsApp; delivered to a holding place; manual quantities without history |
| COS-01, COS-02 | item cost (Setup → Items), monthly labour / rent / other per location |
| COS-03..06, COS-09 | Costs: each count period, month, location or whole business; profit only when no cost line is missing |
| COS-07 | business COGS range; flagged days |
| COS-08 | `view_costs` permission; others never receive cost figures |
| CLS-01..09 | Closing: name, date, location, expected stock, counts, sales by type, issues, check, submit; one per day |
| QR-03 | measured on the ops screen (`/ops/`, request → answer p95) |
| QR-07 | `scripts/run.sh backup` (every service database + Nexus) |

## Enterprise round - warehouse, delivery, inventory control, messages, public page

| ID | What | Where |
|---|---|---|
| WH-01 | bins per location (code, zone), lots put away into bins | warehouse-service `SAVE_BIN`, `MOVE_LOT`; Warehouse floor → Bins, Lots |
| WH-02 | every stock change is filed as lots (expiry from the line, else the item's shelf life; send / transfer carry the expiry) | warehouse-service `jobs.follow_stock` (follows ACCEPTED stock requests; replays history on first start) |
| WH-03 | pick lists: first expiry, first out, walked in bin order; completing one sends the stock | warehouse-service `CREATE_PICK`, `PICK`, `COMPLETE_PICK` → stock SEND; Warehouse floor → Pick lists |
| WH-04 | receive with expiry, batch and bin; barcode scanning of items | Warehouse in (line extras), kit `ItemPalette` scan button; item `barcode`, `shelf_life_days` |
| WH-05 | waste with a reason (expired, spoiled, damaged, made too much, other); in the cost of goods everywhere | stock-service `WASTE`; costing-service; Transfer & adjust → Throw away, lot "Throw away" |
| DEL-01 | delivery runs: the day's trips onto runs, driver, vehicle, stop order, ETA (drive + service minutes) | delivery-service `PLAN_RUN`, `SET_STOPS`; Delivery runs board and run page (drag to reorder) |
| DEL-02 | the driver's phone screen: start, arrive, proof of delivery (receiver + signature) or a problem | delivery-service `START_RUN`, `ARRIVE`, `DELIVER` (→ stock DELIVERED), `FAIL_STOP`; My deliveries |
| INC-01 | minimum / maximum per item and location; below minimum raises an alert with what to fill to | inventory-service `SET_PAR`; Inventory control → Min / max |
| INC-02 | alerts: expired, below zero, expiring in 2 days, below minimum; checked hourly; owners get one email + WhatsApp a day with the new ones | inventory-service `jobs.handle_tick` (schedule `inventory-alerts`), template `stock_alert` |
| INC-03 | stock takes, optionally blind; finishing corrects stock (ADJUST) and keeps the variance and its value | inventory-service `START_TAKE` … `FINISH_TAKE`; Inventory control → Stock take |
| INC-04 | valuation at item cost and by lot cost; ABC by usage value (80 / 95 %), days of cover, waste by reason | inventory-service `VALUATION`, `ANALYSIS`; Valuation, ABC & cover |
| MSG-01 | purchase order sent to the supplier by email, WhatsApp and / or SMS | purchase-service `SEND`, template `purchase_order`; order page → Send to supplier |
| MSG-02 | the business's outbox; test mode = no provider keys, messages are logged (delivery LOGGED) and shown, not sent | notification-service; Outbox |
| WEB-01 | public product page at `#/welcome` (visitors to `/` land there) with a "request a demo" form | `landing.js`; BFF `/public/demo` (3 per 10 minutes per address, hidden bot field) → lead-service |
| WEB-02 | demo requests for the operator, with a stage (new, contacted, won, lost); emailed to `LEADS_NOTIFY_EMAIL` | lead-service (common); Platform → Demo requests |

## Money round - invoices, supplier bills, statements, monthly summary

PDFs use fpdf2 (LGPL, github.com/py-pdf/fpdf2) in kitchen-bff `src/documents/`; amounts are whole cents rounded half-up by `grepx-money`.

| ID | What | Where |
|---|---|---|
| MON-01 | customers (email, address, payment terms) | billing-service `SAVE_CUSTOMER`; Invoices → Customers |
| MON-02 | invoices: draft, then issued with a gapless number per year (INV-YYYY-NNNN), due date from the terms, emailed with a PDF | billing-service `SAVE_INVOICE`, `ISSUE_INVOICE`, template `customer_invoice`; BFF `/sales/invoices/{id}/pdf` |
| MON-03 | sales prices on items prefill invoice lines | item-service `price` ("Sells for" in Setup → Items) |
| MON-04 | an invoice issued from a location takes the goods out of its stock, counted as used (cost of goods, inventory) | billing-service → stock-service `SELL` (movement `sale`); costing, inventory count `sale` |
| MON-05 | payments (part or full), void, credit notes (CN-YYYY-NNNN, full or by line); ageing of what customers owe | billing-service `RECORD_PAYMENT`, `VOID_INVOICE`, `CREDIT_NOTE`, `SUMMARY` |
| MON-06 | customer statement: invoices, credit notes and payments with a running balance, ageing, open invoices; print / PDF | billing-service `STATEMENT`; Customers → Statement (`#/sales/customer/:id`) |
| MON-07 | payment reminders: by hand from an invoice, or automatically at 1, 7, 14 and 30 days late (once each, latest step only) when the business turns it on | billing-service `SEND_REMINDER`, `jobs.tick` (schedule `billing-reminders`, 01:00 UTC), template `payment_reminder`; Setup → Business |
| MON-08 | supplier bills from a received order, three-way matched (ordered / received / billed, price within 2 %); a mismatch needs a note to approve; duplicate supplier refs refused | payables-service `SAVE_BILL`, `APPROVE_BILL`, `RECORD_PAYMENT`, `VOID_BILL`, `SUMMARY`; Supplier bills |
| MON-09 | monthly money summary for the owner: sales and purchases before tax, gross profit (sales less purchases), tax charged / paid / to pay, money in and out; CSV | billing-service and payables-service `MONTHLY`; BFF `/money/report`; Money → Summary (`#/money/report`) |
| MON-10 | profit per product and per customer for a period (this month, last month, quarter, year or dates): sales after discounts less credit notes, cost = quantity x the item's cost today or, for a product made in-house, its recipe's ingredient cost per unit; flags products sold below cost or with no cost | billing-service `MARGINS`; BFF `/money/margins`; Money → Profit (`#/money/margins`) |
| WH-06 | 3D warehouse (WebGL, three.js r170 vendored, MIT): racking with cartons by stock, colour by expiry, beacons on expired bins, search / expiry filter, tour of problem bins, top view, full screen; simple CSS view without WebGL | `warehouse/view3d.js`, `warehouse/scene/*`; Warehouse floor → 3D view |

## Future scope (section 12) - not built
F1 Square, F2 AI entry, F3 full recipe use and batch cost, F4 forecasts from sales, F5 partner stock sharing, ~~F6 expiry~~ (built: WH-02, INC-02),
F7 HR / scheduling, F8 supplier bidding, F9 delivery apps, F10 analytics, ~~F11 margin per product~~ (built: MON-10), F12 customer features.
