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
| Branding: logo on documents | ⬜ | PDFs use the legal name only - **NEXT (with the PDF round)** |
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
| Purchase orders: save, change, copy, cancel, send by email / WhatsApp / SMS | ✅ | Orders |
| Purchase order PDF | ⬜ | **NEXT (PDF round)** |
| Orders list: stage tabs, search, supplier and date filters, prev / next, J / K keys; board cards open a side drawer | ✅ | Orders → Board, List |
| Order timeline (made, sent, received, billed, approved, paid) and ordered-against-received lines | ✅ | order page, drawer, list |
| Goods receipt: in full or changed, expiry, batch, bin | ✅ | Warehouse in |
| Supplier bills, three-way match, approval with note on mismatch, payments | ✅ | Supplier bills |
| Supplier price history and price-jump alerts | ⬜ | step 4 of the plan |
| Purchase approval above an amount set by the owner | ⬜ | |
| Supplier portal, bidding | 🔒 | F5 / F8: needs the business's sharing rules |

## 5. Stock and warehouse
| Feature | Status | Where / what is missing |
|---|---|---|
| Stock per location, every movement kept (who, when, before / after, cost) | ✅ | |
| Receive, send, transfer, adjust (with reason), waste (with reason) | ✅ | |
| Lots, expiry, first-expiry-first-out, bins and zones | ✅ | Warehouse floor |
| Pick lists in bin order | ✅ | |
| Pick list PDF | ⬜ | **NEXT (PDF round)** |
| Min / max per item and place, alerts (out of stock, low, below zero, expiring, expired) sent to the owner by email / WhatsApp / SMS | ✅ | Inventory control; channels in Outbox → What goes out |
| Stock takes (blind), variance and its value | ✅ | |
| Stock take sheet PDF (to count on paper) and result PDF | ⬜ | **NEXT (PDF round)** |
| Valuation (item cost, lot cost), ABC, days of cover, waste by reason | ✅ | |
| 3D warehouse: racks, cartons, expiry, fill, pick routes, keys, snapshot | ✅ | |
| Barcode scanning | ✅ | camera scan in item pickers |

## 6. Delivery to outlets and customers
| Feature | Status | Where / what is missing |
|---|---|---|
| Delivery runs (driver, vehicle, stop order, ETA) | ✅ | Delivery runs |
| Driver phone screen, proof of delivery with signature | ✅ | My deliveries |
| Delivery note PDF with the signature | ⬜ | **NEXT (PDF round)** |

## 7. Closing the day (end of day)
| Feature | Status | Where / what is missing |
|---|---|---|
| Closing: counts, sales by type, issues, one per day, review | ✅ | Closing |
| Closing report PDF with every detail (counts vs system, variances and value, sales, waste, issues, who) | ⬜ | **NEXT (PDF round - first)** |
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
| Quotations for catering events | ⬜ | |
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
| Payslip PDF sent by email / WhatsApp; staff see their own payslips | ⬜ | with the PDF round / mobile app |
| Staff see their own shifts and payslips; mobile app screens | ⬜ | at the end, with the mobile app |

## 10. Messages (email, WhatsApp, SMS)
| Feature | Status | Where / what is missing |
|---|---|---|
| Email (SMTP), WhatsApp (Twilio or Meta Cloud API), SMS (Twilio); test mode logs instead of sending | ✅ | notification-service |
| Operator connects providers, tests the connection, sends a test message; keys sealed | ✅ | Integrations page (platform admin) |
| Each business chooses which automatic messages go out, on which channels, in its own words | ✅ | Outbox → What goes out |
| Failed sends tried again by themselves (5 min, 30 min, 2 h), "Try again now", tries shown | ✅ | Outbox → Sent |
| Files attached to emails (PDFs) | ✅ | used by the PDF round |
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
| Approval inbox (bills to approve, mismatches) | ⬜ | |
| Several languages | ⬜ | English only |
| Assistant: ask in your own words (stock, expiry, how much of X, orders, what to order, who owes, bills, month, best dishes, forecast, cooking, deliveries, open a page); cached answers; permissions respected | ✅ | chat button on every page, Ctrl+J |
| Assistant backed by an AI model (free-form questions) | 🔒 | needs an AI key and the owner's consent; the assistant has the slot for it |

## How each feature is built
Each service owns its tables; business rules are plain tested functions in `domain/`; one module per action in
`routes/`; small classes (Strategy for interchangeable methods, Template Method for documents and reports);
the BFF only joins and checks access; the web is split into small modules. Nothing is marked ✅ before its tests pass.
