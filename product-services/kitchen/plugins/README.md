<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->

# Kitchen plugins

Product rules the generic services load by name (deployment.yaml `plugins:`). The kitchen product needs none yet: its
rules live in its own services (business, item, stock, purchase, planning, closing, costing).

`purchasing_kitchen` also answers payables-service (supplier bills, shared): `set_costs` (an approved bill's landed costs become item costs) and `send_back` (goods returned leave stock).
