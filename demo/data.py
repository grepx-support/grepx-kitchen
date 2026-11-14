# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Demo business 1: a small taco company in Sydney - places, people, suppliers, items, recipes, prices, invoices.
(india.py has the same names for the Indian restaurant; every demo step reads one of them.)

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
WHOLESALE = {"birria": 38.5, "pollo": 36.0, "consomme": 4.5}   # what a box / cup sells for on an invoice to cafes and caterers
DAILY_SALES = {"bondi": {"birria": 14, "pollo": 10, "consomme": 12},   # usual units sold a day (varied by the seed)
               "parra": {"birria": 10, "pollo": 9, "consomme": 8},
               "truck": {"birria": 18, "pollo": 6, "consomme": 15}}
OVERHEADS = {"bondi": (6200, 3800, 600), "parra": (5400, 3200, 500), "truck": (4100, 900, 700), "kit": (7000, 2600, 400)}

KEY = "taco"
PHONE = "+614000000{n}"                    # staff phone numbers (n = 10, 11, ...)

# what the steps do with the data
PACKAGING = ("pack", {"box": 6})          # the packaging supplier gets a fixed order every buying day
ISSUES = ["", "", "", "", "Fridge door not closing properly", "Ran out of coriander at 7pm", "Card machine slow"]
MARKET = [("coriander", 6, 1, "MKT-1", "C-02"), ("cheese", 4, None, "OX-2207", "C-02")]   # (item, qty, expires in days, lot, bin)
WASTE = [("coriander", 2, "spoiled"), ("tortilla", 1, "damaged"), ("birria", 3, "overproduced")]
PICK = [("tortilla", 6), ("box", 4), ("coriander", 3)]                                   # for the last seller (the truck)
RUN = {"name": "Eastern suburbs", "vehicle": "Van 1", "start_time": "10:30"}

BILLING = {"legal_name": "Demo Taco Co Pty Ltd", "address": "12 Harbour Road\nSydney NSW 2000", "tax_label": "GST", "tax_number": "51 824 753 556",
           "tax_rate": 10, "payment_note": "Bank transfer to BSB 062-000, account 1234 5678, or PayID accounts@demo-taco.test. Please quote the invoice number."}
CUSTOMERS = [("Cafe Uno", "accounts@cafeuno.test", 14, "8 Pitt Street\nSydney NSW 2000"),
             ("Harbourside Catering", "ap@harbourside.test", 30, "2 Wharf Lane\nPyrmont NSW 2009"),
             ("Taco Tuesday Franchise", "finance@tacotuesday.test", 7, "77 King Street\nNewtown NSW 2042")]
INVOICES = [  # customer, days ago, lines [(item key or description, qty, price)], paid share (0..1, None = leave as draft)
    (0, 40, [("birria", 30, "38.50"), ("Delivery", 1, "15")], 1.0),
    (1, 20, [("pollo", 24, "36.00"), ("Catering staff (hours)", 6, "45")], 0.5),
    (2, 25, [("birria", 12, "38.50"), ("pollo", 12, "36.00")], 0.0),
    (0, 3, [("birria", 18, "38.50")], 0.0),
    (1, 0, [("pollo", 10, "36.00")], None),
]
BILL_REF = "SUP-{n}"

# Funds: partners and an investor (one promise overdue, one paid in NZ dollars), money put to the places by their names
# (so Funds shows each place's real costs against it), and a small equipment loan.
FUND_PARTIES = [("Olivia Owner", "owner", "owner@demo-taco.test", "+61400000001"), ("Liam Chen", "partner", "liam@demo-taco.test", "+61400000002"),
                ("Harbour Angels", "investor", "hello@harbour-angels.test", ""), ("Kiwi Kitchen Fund", "investor", "invest@kiwikitchen.test", ""),
                ("Westpac", "lender", "business@westpac.test", "")]
FUNDS = [("Founders' capital", "equity", 600000, 0, [
            ("commit", 250000, "Olivia Owner", 210, 190), ("commit", 150000, "Liam Chen", 210, 160), ("commit", 120000, "Harbour Angels", 80, 15),
            ("commit", 92000, "Kiwi Kitchen Fund", 60, -45),
            ("receive", 250000, "Olivia Owner", 195, ""), ("receive", 150000, "Liam Chen", 170, ""), ("receive", 50000, "Harbour Angels", 55, ""),
            ("receive", 50000, "Kiwi Kitchen Fund", 50, "", {"currency": "NZD", "rate": "0.92", "ref": "TT KKF-114"}),
            ("allocate", 160000, "", 180, "Taco kitchen"), ("allocate", 45000, "", 150, "Bondi store"), ("allocate", 60000, "", 110, "Parramatta store"),
            ("allocate", 35000, "", 45, "Food truck"), ("spend", 120000, "", 170, "Taco kitchen"), ("cost", 1800, "", 140, "")]),
         ("Equipment loan", "loan", 0, 8.9, [
            ("receive", 80000, "Westpac", 140, ""), ("allocate", 72000, "", 135, "Food truck"),
            ("interest", 593, "Westpac", 110, ""), ("return", 4000, "Westpac", 110, ""), ("interest", 563, "Westpac", 80, ""), ("return", 4000, "Westpac", 80, ""),
            ("interest", 533, "Westpac", 50, ""), ("return", 4000, "Westpac", 50, "")])]
FUND_PLANS = {"Founders' capital": {"horizon": 36, "discount_pct": 12, "payout_pct": 50, "hurdle_pct": 15, "uses": [
    {"purpose": "Bondi store", "monthly_ebitda": 9000, "starts_in": 0, "ramp": 3}, {"purpose": "Parramatta store", "monthly_ebitda": 7000, "starts_in": 1, "ramp": 4},
    {"purpose": "Food truck", "monthly_ebitda": 3500, "starts_in": 1, "ramp": 3}]}}
