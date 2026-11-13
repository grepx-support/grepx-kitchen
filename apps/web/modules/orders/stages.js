/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Where an order stands, as the screens name and colour it (the BFF works the stage out from the order and its bills).
import { pill } from "/assets/kit/index.js";

export const STAGES = {
  on_order: { label: "On order", tone: "warn", icon: "clock", colour: "#7c3aed" },
  received: { label: "Received", tone: "info", icon: "inbox", colour: "#0ea5e9" },
  billed: { label: "Billed", tone: "warn", icon: "receipt", colour: "#f59e0b" },
  paid: { label: "Paid", tone: "good", icon: "check", colour: "#16a34a" },
  cancelled: { label: "Cancelled", tone: "", icon: "x", colour: "#94a3b8" },
};

export const stagePill = (stage) => pill(STAGES[stage]?.label || stage, STAGES[stage]?.tone || "");
