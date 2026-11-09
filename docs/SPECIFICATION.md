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

## Future scope (section 12) - not built
F1 Square, F2 AI entry, F3 full recipe use and batch cost, F4 forecasts from sales, F5 partner stock sharing, F6 expiry,
F7 HR / scheduling, F8 supplier bidding, F9 delivery apps, F10 analytics, F11 margin per product, F12 customer features.
