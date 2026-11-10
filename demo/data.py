# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The demo business: a small taco company in Sydney - places, people, suppliers, items, recipes, prices.

Every login uses PASSWORD. It is demo data: never reuse these logins or this password for a real business.
"""

BUSINESS = {"name": "Demo Taco Co", "currency": "AUD", "timezone": "Australia/Sydney"}
PASSWORD = "Demo-Kitchen-2026"
OWNER = {"name": "Olivia Owner", "email": "owner@demo-taco.test", "phone": "+61400000001"}

# (key, name, kind, holding, address)  - addresses put the places on the live operations map
PLACES = [
    ("wh", "Central warehouse", "warehouse", True, "Alexandria NSW 2015, Australia"),
    ("kit", "Taco kitchen", "kitchen", False, "Marrickville NSW 2204, Australia"),
    ("bondi", "Bondi store", "store", False, "Bondi Beach NSW 2026, Australia"),
    ("parra", "Parramatta store", "store", False, "Parramatta NSW 2150, Australia"),
    ("truck", "Food truck", "truck", False, "Sydney Olympic Park NSW 2127, Australia"),
]
SELLERS = ["bondi", "parra", "truck"]

# (staff role, name, email) - what each one sees is set by their role
STAFF = [
    ("warehouse", "Wes Warehouse", "wes@demo-taco.test"),
    ("kitchen", "Kim Kitchen", "kim@demo-taco.test"),
    ("closing", "Tia Closing", "tia@demo-taco.test"),
    ("delivery", "Dan Driver", "dan@demo-taco.test"),
]

SUPPLIERS = [
    ("meat", "Harbour Meats", "+61400111222", "Sam"),
    ("veg", "Green Valley Produce", "+61400333444", "Priya"),
    ("dry", "Golden Bakery & Dry Goods", "+61400555666", "Leo"),
    ("pack", "Pack & Co", "+61400777888", "Mia"),
]
SUPPLIER_EMAIL = "orders@{key}.demo-taco.test"     # demo addresses (.test never delivers)

# days an item keeps once received (dates its lots) and a made-up barcode for the scanner
SHELF_LIFE = {"beef": 5, "chicken": 4, "tortilla": 10, "onion": 14, "coriander": 4, "cheese": 21, "chilli": 180}
BARCODE = {"beef": "9300000000011", "chicken": "9300000000028", "tortilla": "9300000000035", "cheese": "9300000000042", "box": "9300000000059"}

# warehouse floor: bins of the central warehouse (code, zone) and minimum / maximum per item there
BINS = [("C-01", "chilled"), ("C-02", "chilled"), ("D-01", "dry"), ("D-02", "dry"), ("F-01", "frozen")]
BIN_OF = {"beef": "C-01", "chicken": "C-01", "cheese": "C-02", "coriander": "C-02", "tortilla": "D-01", "chilli": "D-02", "onion": "D-02", "box": "D-01"}
PAR = {"beef": (25, 60), "chicken": (20, 50), "tortilla": (30, 80), "chilli": (2, 5), "onion": (10, 30), "coriander": (12, 40),
       "cheese": (8, 20), "box": (15, 40)}

# (key, name, kind, unit, cost, supplier key, category)
ITEMS = [
    ("beef", "Beef chuck", "ingredient", "kg", 14.0, "meat", "Meat"),
    ("chicken", "Chicken thigh", "ingredient", "kg", 9.5, "meat", "Meat"),
    ("tortilla", "Corn tortillas", "ingredient", "pack", 4.5, "dry", "Bakery"),
    ("chilli", "Guajillo chilli", "ingredient", "kg", 22.0, "dry", "Dry goods"),
    ("onion", "Onion", "ingredient", "kg", 2.2, "veg", "Produce"),
    ("coriander", "Coriander", "ingredient", "bunch", 1.6, "veg", "Produce"),
    ("cheese", "Oaxaca cheese", "ingredient", "kg", 13.0, "dry", "Dairy"),
    ("box", "Takeaway boxes", "supply", "pack", 6.0, "pack", "Packaging"),
    ("birria", "Birria tacos", "finished", "box", 5.1, "", "Tacos"),      # costs = the recipe's ingredients per unit
    ("pollo", "Chicken tacos", "finished", "box", 3.95, "", "Tacos"),
    ("consomme", "Consomme", "finished", "cup", 0.65, "", "Sides"),
]

# product -> (one batch makes, {ingredient: qty per batch})
RECIPES = {
    "birria": (20, {"beef": 5, "chilli": 0.4, "onion": 1, "tortilla": 4, "coriander": 2}),
    "pollo": (20, {"chicken": 4.5, "onion": 0.8, "tortilla": 4, "cheese": 1, "coriander": 2}),
    "consomme": (30, {"beef": 1, "chilli": 0.2, "onion": 0.5}),
}

PRICE = {"birria": 18.0, "pollo": 15.0, "consomme": 4.5}       # sale price, for the closing's sales figure
DAILY_SALES = {"bondi": {"birria": 14, "pollo": 10, "consomme": 12},   # usual units sold a day (varied by the seed)
               "parra": {"birria": 10, "pollo": 9, "consomme": 8},
               "truck": {"birria": 18, "pollo": 6, "consomme": 15}}
OVERHEADS = {"bondi": (6200, 3800, 600), "parra": (5400, 3200, 500), "truck": (4100, 900, 700), "kit": (7000, 2600, 400)}
