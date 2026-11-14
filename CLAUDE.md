<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->

# Working on this repository (read first)

This is the **kitchen** product on the GrepX platform, and the workspace it runs from. The platform rules are in
`docs/platform/` (linked from grepx-platform): `CLAUDE.md`, `ARCHITECTURE.md`, `DEVELOPMENT-GUIDE.md`.
What the product must do and where each requirement lives: `docs/SPECIFICATION.md`.

Hard rules (on top of the platform's)
- Every kitchen row carries `tenant_id` = the business. The BFF takes it from the login token (`Kitchen.cmd`), never from
  the client, and every read filters by it. A service treats a row of another business as not there.
- Business rules live in the owning service's `src/domain/` (stock, planning, costing, closing...), never in the BFF or UI.
- Business owners are role `staff` with their business's `owner` staff role; role `admin` is the platform operator only.
- Staff roles are per business (`<tenant>.<role>`), copied from `product-services/kitchen/catalog/access.yaml`.
- Run `scripts/run.sh test` before committing. Commits end with the attribution lines the session asks for.
