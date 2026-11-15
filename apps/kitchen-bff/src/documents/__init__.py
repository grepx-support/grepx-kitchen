# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen documents: the shared PDF kit (grepx_bff.documents) plus the kitchen's own working-document specs."""
from grepx_bff.documents import BillPdf, InvoicePdf, PdfFile, QuotePdf, ReportPdf, brand, render

from . import specs

__all__ = ["brand", "BillPdf", "InvoicePdf", "PdfFile", "QuotePdf", "ReportPdf", "render", "specs"]
