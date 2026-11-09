<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->

# grepx-kitchen

**Kitchen Stock & Costing** on the GrepX platform - kitchen production, stock, supplier orders, daily cost and staff
closing for food businesses, many businesses on one system (first client: Halal Fusion Taco). This repo is also the
workspace you run it from.

| Folder | What |
|---|---|
| `product-services/kitchen/` | the kitchen services (below), `deployment.yaml` (how kitchen plugs into the common services, the live screen), `catalog/` (permissions, staff-role templates, message templates) |
| `apps/kitchen-bff/` | JSON API `/api/v1` for the web and mobile apps; every request is scoped to the user's business |
| `apps/web/` | the kitchen screens (`modules/`) and brand (`product.json`) for the shared web shell (`web/`, from grepx-platform) |
| `apps/mobile/` | the Flutter phone app (Android + iOS) |
| `config/` | `common.yaml` (Nexus on port **7880**), `services.ini` (what runs, ports **93xx / 94xx / 8861**), `projects/` |
| `docs/SPECIFICATION.md` | every BRD requirement and where it is built; the open questions and the answers used |

Kitchen runs its own Nexus hub and its own ports, so it can share a server with another GrepX product (blood donation
uses 7878 / 88xx-91xx / 8851).

## Services

| Service | Owns | Does |
|---|---|---|
| business-service | businesses, locations | a business = a tenant (currency, time zone, modules on/off, planning and costing settings); kitchens, warehouses, stores, trucks |
| item-service | items, suppliers, recipes | ingredients / finished products / supplies with unit and cost; suppliers; batch output + optional ingredient list |
| stock-service | stock_levels, stock_movements | receive, warehouse out, transfer, production, ingredient use, adjustment (with reason), count - every change with who, when, why and cost; history is append-only |
| purchase-service | purchase_orders | save, change, copy, cancel, receive (adds stock at the holding place); WhatsApp text |
| planning-service | plans | production target, warehouse out / in suggestions, reorder recommendation (previous one shown, large changes flagged), manual targets |
| closing-service | closings | the staff closing; its count replaces system stock |
| costing-service | cost_days, overheads | COGS per count period, costing average, COGS range alert, monthly summary (no profit while a cost is missing) |

Reused common services: identity (auth, access), people, notification, template, scheduler, task, audit-log, settings,
ops-monitor (live screen at `/ops/`).

## Set up (via the orchestrator)

```bash
cd ~/grepx-database-server-orchastrator && ./install.sh kitchen
```

By hand: the other repos sit next to this one (`../grepx-platform ../grepx-services ../grepx-nexus-cpp`), then
`./deploy.sh` (or `./workspace.sh`, `scripts/setup.sh`, `scripts/run.sh start && scripts/run.sh seed`).

Then create the platform operator (GrepX staff) and open `http://<server>:8861/`:

```bash
scripts/run.sh admin you@grepx.sg 'Password-1' 'Your Name' '+6591234567'
```

The operator creates each business and its owner on the **Businesses** page; the owner sets up locations, items,
suppliers, recipes, users and roles under **Setup**.

## Phone app

```bash
cd apps/mobile && ./setup.sh
flutter build apk --release --dart-define=API_BASE=https://your.kitchen.domain
```
GitHub Actions builds the APK on every push that touches `apps/mobile/` (`.github/workflows/mobile.yml`; set the
repository variable `API_BASE`).
