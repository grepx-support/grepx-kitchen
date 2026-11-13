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
| Multi-factor login, single sign-on | 🔒 | needs a decision on the provider |
| Login history / user activity | 🟡 | every stock movement keeps who and when; no login-history screen |

## 2. Menu, recipes and costing (F&B extension)
| Feature | Status | Where / what is missing |
|---|---|---|
| Items: ingredients, made products, supplies; unit, barcode, shelf life, sale price | ✅ | Setup → Items |
| Recipes (ingredients per batch, batch size) | ✅ | Setup → Recipes |
| Cost per portion from the recipe | ✅ | used by Profit by product |
| Recipe cost card (line by line, cost history) | ⬜ | **NEXT (step 2 of the plan)** |
| Menu engineering (stars / plough-horses / puzzles / dogs) | ⬜ | **NEXT (step 2)** |
| Allergens and dietary tags on dishes | ⬜ | |
| Several units per item (case of 12 = 12 each) | ⬜ | one unit per item today |

## 3. Kitchen production
| Feature | Status | Where / what is missing |
|---|---|---|
| Weekly production target from usage, safety %, event extra | ✅ | Kitchen screen |
| Record batches made; ingredients used come off stock | ✅ | Kitchen screen, Terminal |
| Kitchen terminal (big screen, timers) | ✅ | Terminal |
| Forecast per dish per outlet per day, most accurate method chosen | 🟡 | forecast-service built and tested; page and "use as targets" - **NEXT (now)** |
| Prep lists per station / shift | ⬜ | |
| Food safety records (fridge temperatures, cleaning checks, HACCP) | ⬜ | |

## 4. Buying (procure to pay)
| Feature | Status | Where / what is missing |
|---|---|---|
| Suppliers (contact, phone, email) | ✅ | Setup → Suppliers |
| Recommended orders per supplier from usage | ✅ | Orders → Recommended |
| Purchase orders: save, change, copy, cancel, send by email / WhatsApp / SMS | ✅ | Orders |
| Purchase order PDF | ⬜ | **NEXT (PDF round)** |
| Orders list: status tabs, search, supplier and date filters, sort, prev / next, keys | 🟡 | a board exists - **NEXT (orders navigation round)** |
| Order timeline (made, sent, received, billed, paid) | ⬜ | **NEXT (orders navigation round)** |
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
| Min / max per item and place, alerts (expired, low, below zero, expiring) | ✅ | Inventory control |
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
| Staff rostering, rostered hours as labour cost | ⬜ | step 3 of the plan (roster-service) |
| Clock in / out, leave, payroll | ➖ | the general ERP's HR / payroll modules |

## 10. Experience
| Feature | Status | Where / what is missing |
|---|---|---|
| Ctrl+K search over pages, actions and records; G + letter; ? for keys | ✅ | |
| Pinned pages (star), Alt+1-9, folding menu groups | ✅ | |
| Dark and light theme, phone layouts | ✅ | |
| Sortable tables, CSV download where it matters | 🟡 | sorting everywhere; CSV on the money summary only |
| Saved filters per table | ⬜ | |
| Activity timeline on records | ⬜ | orders first - **NEXT** |
| Approval inbox (bills to approve, mismatches) | ⬜ | |
| Several languages | ⬜ | English only |
| AI assistant (ask questions of the data) | 🔒 | F2: needs an AI key and the owner's consent |

## How each feature is built
Each service owns its tables; business rules are plain tested functions in `domain/`; one module per action in
`routes/`; small classes (Strategy for interchangeable methods, Template Method for documents and reports);
the BFF only joins and checks access; the web is split into small modules. Nothing is marked ✅ before its tests pass.
