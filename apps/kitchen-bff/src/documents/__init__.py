# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Printable documents (PDF, rendered with the open-source fpdf2 library: https://github.com/py-pdf/fpdf2, LGPL-3.0)."""
from .invoice import BillPdf, InvoicePdf, render

__all__ = ["BillPdf", "InvoicePdf", "render"]
