# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bulk import / export of records from Excel or CSV - one Importer per kind (Strategy), looked up by its name."""
from .base import Column, Importer, Prepared
from .catalogue import Items, Suppliers
from .opening_stock import OpeningStock
from .recipes import Recipes
from .team import Employees

IMPORTERS = {i.kind: i for i in (Suppliers(), Items(), Recipes(), OpeningStock(), Employees())}

__all__ = ["IMPORTERS", "Column", "Importer", "Prepared"]
