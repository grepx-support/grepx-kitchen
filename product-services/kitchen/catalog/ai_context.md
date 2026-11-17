<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->
# GrepX Kitchen - what the AI should know

GrepX Kitchen runs a central kitchen with a warehouse and the outlets (stores, food trucks, catering) it supplies: buying
ingredients, keeping stock by lot and expiry, producing dishes and batches, sending them to outlets, closing each day,
and knowing the food cost. Money is in the business's currency (often SGD or AUD).

## Words
- **Item** - anything stocked: an ingredient (beef, flour), packaging, or something the kitchen makes (sauce, dish).
- **Recipe** - what an item is made of, per batch; **production** - making items from ingredients (the ingredients are used up).
- **Lot** - one delivery or batch of an item with its own expiry; stock is used **first expiry first out (FEFO)**.
- **Warehouse out / in** - stock sent from the holding place to an outlet, and received there. **Transfer** - outlet to outlet.
- **Waste** - thrown away with a reason (expired, spoiled, damaged, overproduced). **Count** - a stock count at closing.
- **Closing** - the end of a day at an outlet: count, sales, issues. **COGS / food cost %** - ingredient cost of what was
  sold divided by sales; the business sets the range it expects.
- **Par level** - the stock an outlet should start the day with; the **reorder recommendation** fills the gap.
- **Purchase order** to a supplier, **delivery** received (by lot), **supplier bill** matched to order and delivery.

## Where things are (menu)
- Home: brief, food cost, money, kitchen plan, what is needed, orders, deliveries, closings.
- Kitchen: production plan and recording what was made and used. Stock: levels, warehouse in/out, transfers, waste.
- Warehouse: bins, lots and expiry, pick lists, the 3D floor. Orders: reorder recommendation and purchase orders.
- Closing: the day's count, sales and issues. Costs: food cost by day and month, overheads, labour.
- Money: customers, invoices, supplier bills, payments. People: team, roster, leave, payroll. Setup: business, items, recipes, users.

## How-to (short)
- Lots expiring soon: Warehouse -> lots (sorted by expiry); use them first or move them to an outlet that needs them.
- Waste is high: look at waste by item and reason; overproduced means the production plan is above what sells.
- Food cost out of range: Costs -> day; check items without a cost and big waste days first.
- Reorder: Orders -> recommendation, then make the purchase orders; receive deliveries by lot with their expiry.

## Rules for answers
Answer from the business data given. Say what is missing rather than guess. Use the business's currency. Keep answers
short and practical for a busy chef, store manager or owner; point to the screen where they can act.
