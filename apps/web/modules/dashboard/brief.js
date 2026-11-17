/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The morning brief (shared: modules/business/widgets/brief.js): expiring lots, waste, food cost, orders - AI-written when on.
import { briefWidget } from "/assets/modules/business/widgets/brief.js";
import { can } from "/assets/app.js";

export default briefWidget({ allowed: () => ["view_stock", "view_costs", "manage_business", "kitchen"].some((p) => can(p)),
  example: "what did we waste most this month and why?" });
