# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Demo business 2: Spice Route Kitchen, an Indian restaurant group in Mumbai - a central kitchen cooking biryani, curries
and naan for two outlets and a tiffin van, wholesale catering customers, GST at 5 %, money in rupees.
Same names as data.py (the taco demo); every login uses PASSWORD. Demo data only: .test addresses never deliver.
"""
from data import PASSWORD  # noqa: F401  (one demo password for every demo business)

KEY = "india"
BUSINESS = {"name": "Spice Route Kitchen", "currency": "INR", "timezone": "Asia/Kolkata"}
OWNER = {"name": "Aarav Mehta", "email": "owner@spice-route.test", "phone": "+919800000001"}
PHONE = "+9198000000{n}"

PLACES = [
    ("wh", "Central store - Andheri", "warehouse", True, "Andheri East, Mumbai 400069, India"),
    ("kit", "Central kitchen - Powai", "kitchen", False, "Powai, Mumbai 400076, India"),
    ("bandra", "Bandra outlet", "store", False, "Bandra West, Mumbai 400050, India"),
    ("parel", "Lower Parel outlet", "store", False, "Lower Parel, Mumbai 400013, India"),
    ("van", "Tiffin van", "truck", False, "Bandra Kurla Complex, Mumbai 400051, India"),
]
SELLERS = ["bandra", "parel", "van"]

STAFF = [
    ("warehouse", "Ravi Kumar", "ravi@spice-route.test"),
    ("kitchen", "Meera Iyer", "meera@spice-route.test"),
    ("closing", "Sneha Patil", "sneha@spice-route.test"),
    ("delivery", "Arjun Singh", "arjun@spice-route.test"),
]

SUPPLIERS = [
    ("meat", "Deonar Fresh Meats", "+919811122233", "Imran"),
    ("veg", "Vashi Sabzi Mandi Traders", "+919833344455", "Ganesh"),
    ("dry", "Masala & Grains Co", "+919855566677", "Mr Shah"),
    ("dairy", "Krishna Dairy Supplies", "+919877788899", "Lakshmi"),
    ("pack", "EcoPack Mumbai", "+919899900011", "Neha"),
]
SUPPLIER_EMAIL = "orders@{key}.spice-route.test"

SHELF_LIFE = {"chicken": 3, "mutton": 3, "paneer": 5, "curd": 4, "cream": 7, "tomato": 6, "onion": 20, "coriander": 3,
              "rice": 365, "maida": 120, "dal": 270, "ghee": 180, "masala": 365}
BARCODE = {"chicken": "8900000000011", "paneer": "8900000000028", "rice": "8900000000035", "ghee": "8900000000042", "box": "8900000000059"}

BINS = [("C-01", "chilled"), ("C-02", "chilled"), ("C-03", "chilled"), ("D-01", "dry"), ("D-02", "dry"), ("D-03", "dry"), ("P-01", "packaging"), ("F-01", "frozen")]
BIN_OF = {"chicken": "C-01", "mutton": "C-01", "paneer": "C-02", "curd": "C-02", "cream": "C-02", "tomato": "C-03", "coriander": "C-03",
          "rice": "D-01", "maida": "D-01", "box": "P-01", "dal": "D-02", "ghee": "D-02", "onion": "D-02", "masala": "D-03"}
PAR = {"chicken": (20, 60), "paneer": (8, 25), "rice": (40, 120), "maida": (20, 60), "dal": (10, 40), "onion": (20, 60), "tomato": (15, 45),
       "curd": (8, 25), "cream": (5, 15), "ghee": (5, 15), "masala": (1, 4), "coriander": (15, 50), "box": (10, 30)}

# (key, name, kind, unit, cost in rupees, supplier key, category) - made dishes get their cost from the recipe below
_RAW = [
    ("chicken", "Chicken (curry cut)", "ingredient", "kg", 290, "meat", "Meat"),
    ("mutton", "Mutton", "ingredient", "kg", 750, "meat", "Meat"),
    ("paneer", "Paneer", "ingredient", "kg", 430, "dairy", "Dairy"),
    ("curd", "Curd (dahi)", "ingredient", "kg", 70, "dairy", "Dairy"),
    ("cream", "Fresh cream", "ingredient", "litre", 250, "dairy", "Dairy"),
    ("ghee", "Ghee", "ingredient", "kg", 650, "dairy", "Dairy"),
    ("rice", "Basmati rice", "ingredient", "kg", 130, "dry", "Grains"),
    ("maida", "Maida (flour)", "ingredient", "kg", 40, "dry", "Grains"),
    ("dal", "Black urad dal", "ingredient", "kg", 140, "dry", "Pulses"),
    ("masala", "Garam masala", "ingredient", "kg", 900, "dry", "Spices"),
    ("onion", "Onion", "ingredient", "kg", 35, "veg", "Produce"),
    ("tomato", "Tomato", "ingredient", "kg", 40, "veg", "Produce"),
    ("coriander", "Coriander", "ingredient", "bunch", 10, "veg", "Produce"),
    ("box", "Takeaway containers (50)", "supply", "pack", 180, "pack", "Packaging"),
]
DISHES = [("biryani", "Chicken biryani", "portion", "Rice"), ("butter", "Butter chicken", "portion", "Curries"),
          ("dalmakhani", "Dal makhani", "portion", "Curries"), ("paneer_tikka", "Paneer tikka masala", "portion", "Curries"),
          ("naan", "Butter naan", "piece", "Breads")]

# dish -> (one batch makes, {ingredient: qty per batch})
RECIPES = {
    "biryani": (20, {"chicken": 3.0, "rice": 2.4, "onion": 1.5, "curd": 1.0, "ghee": 0.4, "masala": 0.08, "coriander": 2}),
    "butter": (20, {"chicken": 3.2, "tomato": 2.5, "cream": 1.0, "ghee": 0.3, "onion": 0.8, "masala": 0.06}),
    "dalmakhani": (25, {"dal": 2.0, "cream": 0.8, "ghee": 0.4, "tomato": 1.5, "onion": 0.6}),
    "paneer_tikka": (20, {"paneer": 3.0, "tomato": 2.0, "curd": 0.8, "cream": 0.6, "onion": 1.0, "masala": 0.05}),
    "naan": (50, {"maida": 4.0, "curd": 0.6, "ghee": 0.3}),
}
_COST = {r[0]: r[4] for r in _RAW}
ITEMS = _RAW + [(k, name, "finished", unit, round(sum(q * _COST[i] for i, q in RECIPES[k][1].items()) / RECIPES[k][0], 2), "", cat)
                for k, name, unit, cat in DISHES]

# veg mark and allergens of each ingredient (dishes take theirs from these)
MARKS = {"chicken": ("non_veg", []), "mutton": ("non_veg", []), "paneer": ("veg", ["milk"]), "curd": ("veg", ["milk"]),
         "cream": ("veg", ["milk"]), "ghee": ("veg", ["milk"]), "rice": ("vegan", []), "maida": ("vegan", ["gluten"]),
         "dal": ("vegan", []), "masala": ("vegan", ["mustard"]), "onion": ("vegan", []), "tomato": ("vegan", []), "coriander": ("vegan", [])}
# the chef's card of each dish
CARDS = {
    "biryani": {"station": "rice", "prep_min": 40, "cook_min": 55, "yield_pct": 95, "portion": "350 g handi", "hold_hours": 3,
                "steps": ["Marinate chicken in curd, masala and salt - 2 hours, chilled", "Soak basmati 30 minutes, par-boil to 70%",
                          "Fry onions golden (birista) in ghee", "Layer chicken, rice, birista, coriander", "Seal the handi; dum 25 minutes on low heat"],
                "plating": "Handi with raita and salan on the side; birista and mint on top"},
    "butter": {"station": "curry", "prep_min": 25, "cook_min": 35, "yield_pct": 92, "portion": "250 g bowl", "hold_hours": 4,
               "steps": ["Tandoor the marinated chicken (tikka)", "Cook tomato, butter and cashew-free makhani gravy 20 minutes",
                         "Blend smooth, add cream and kasuri methi", "Fold in the tikka; simmer 5 minutes"], "plating": "Swirl of cream, butter cube"},
    "dalmakhani": {"station": "curry", "prep_min": 15, "cook_min": 240, "yield_pct": 90, "portion": "250 g bowl", "hold_hours": 6,
                   "steps": ["Soak urad dal overnight", "Pressure-cook soft", "Slow-cook 3-4 hours with tomato, butter and cream"]},
    "paneer_tikka": {"station": "tandoor", "prep_min": 30, "cook_min": 20, "yield_pct": 96, "portion": "250 g bowl", "hold_hours": 3,
                     "steps": ["Cube paneer, marinate in curd and masala", "Skewer and tandoor 6-8 minutes", "Finish in masala gravy"]},
    "naan": {"station": "tandoor", "prep_min": 20, "cook_min": 15, "yield_pct": 98, "portion": "1 piece",
             "steps": ["Knead maida, curd, salt; rest 2 hours", "Divide 80 g balls", "Slap on the tandoor wall 90 seconds", "Brush with butter"]},
}

PRICE = {"biryani": 260, "butter": 290, "dalmakhani": 180, "paneer_tikka": 260, "naan": 35}       # menu price at the outlets
WHOLESALE = {"biryani": 240, "butter": 280, "dalmakhani": 190, "paneer_tikka": 250, "naan": 40}   # catering price on invoices
DAILY_SALES = {"bandra": {"biryani": 30, "butter": 22, "dalmakhani": 18, "paneer_tikka": 16, "naan": 70},
               "parel": {"biryani": 24, "butter": 18, "dalmakhani": 15, "paneer_tikka": 12, "naan": 55},
               "van": {"biryani": 40, "butter": 8, "dalmakhani": 10, "paneer_tikka": 6, "naan": 30}}
OVERHEADS = {"bandra": (180000, 250000, 25000), "parel": (150000, 220000, 20000), "van": (60000, 15000, 18000), "kit": (220000, 120000, 30000)}

PACKAGING = ("pack", {"box": 4})
ISSUES = ["", "", "", "", "Tandoor slow to heat up", "Ran out of naan dough at 9pm", "UPI payments slow at lunch", "Delivery-app tablet offline for an hour"]
MARKET = [("coriander", 15, 1, "MKT-1", "C-03"), ("paneer", 5, None, "PN-2207", "C-02")]
WASTE = [("coriander", 3, "spoiled"), ("tomato", 2, "damaged"), ("biryani", 4, "overproduced")]
PICK = [("rice", 10), ("box", 3), ("coriander", 5)]
RUN = {"name": "Western line", "vehicle": "Tempo 1", "start_time": "11:00"}

BILLING = {"legal_name": "Spice Route Kitchen Pvt Ltd", "address": "Unit 4, Marol Industrial Estate\nAndheri East, Mumbai 400059", "tax_label": "GST",
           "tax_number": "27AABCS1234F1Z5", "tax_rate": 5,
           "payment_note": "UPI spiceroute@demo, or NEFT to account 0000 1234 5678 (IFSC DEMO0001234). Please quote the invoice number."}
CUSTOMERS = [("BKC Corporate Cafeteria", "accounts@bkc-cafeteria.test", 15, "Bandra Kurla Complex\nMumbai 400051"),
             ("Shubh Vivah Caterers", "billing@shubhvivah.test", 30, "Dadar West\nMumbai 400028"),
             ("Powai TechPark Canteen", "ap@techpark-canteen.test", 7, "Hiranandani Gardens, Powai\nMumbai 400076")]
INVOICES = [
    (0, 40, [("biryani", 60, "240"), ("Delivery", 1, "500")], 1.0),
    (1, 20, [("butter", 40, "280"), ("naan", 120, "40"), ("Serving staff (hours)", 8, "350")], 0.5),
    (2, 25, [("dalmakhani", 30, "190"), ("paneer_tikka", 25, "250")], 0.0),
    (0, 3, [("biryani", 40, "240")], 0.0),
    (1, 0, [("butter", 20, "280")], None),
]
BILL_REF = "SRK/26-27/{n}"
