"""Action routing for billing-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import BillingAction
from . import save_customer
from . import save_invoice
from . import issue_invoice
from . import record_payment
from . import void_invoice
from . import credit_note
from . import summary
from . import monthly
from . import margins
from . import statement
from . import send_reminder

TABLE = "billing_requests"
ROUTES = {
    BillingAction.SAVE_CUSTOMER: save_customer.handle,
    BillingAction.SAVE_INVOICE: save_invoice.handle,
    BillingAction.ISSUE_INVOICE: issue_invoice.handle,
    BillingAction.RECORD_PAYMENT: record_payment.handle,
    BillingAction.VOID_INVOICE: void_invoice.handle,
    BillingAction.CREDIT_NOTE: credit_note.handle,
    BillingAction.SUMMARY: summary.handle,
    BillingAction.MONTHLY: monthly.handle,
    BillingAction.MARGINS: margins.handle,
    BillingAction.STATEMENT: statement.handle,
    BillingAction.SEND_REMINDER: send_reminder.handle,
}
handle = ActionDispatcher(ROUTES, BillingAction, TABLE)
