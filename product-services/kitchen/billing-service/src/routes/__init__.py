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
from . import save_quote, send_quote, accept_quote, decline_quote, cancel_quote, invoice_order, quotes
from . import prices

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
    BillingAction.SAVE_QUOTE: save_quote.handle,
    BillingAction.SEND_QUOTE: send_quote.handle,
    BillingAction.ACCEPT_QUOTE: accept_quote.handle,
    BillingAction.DECLINE_QUOTE: decline_quote.handle,
    BillingAction.CANCEL_QUOTE: cancel_quote.handle,
    BillingAction.INVOICE_ORDER: invoice_order.handle,
    BillingAction.QUOTES: quotes.handle,
    BillingAction.SET_PRICE_BREAKS: prices.set_breaks,
    BillingAction.PRICE: prices.price,
    BillingAction.PRICE_LIST: prices.price_list,
}
handle = ActionDispatcher(ROUTES, BillingAction, TABLE)
