"""Action routing for payables-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import PayablesAction
from . import save_bill
from . import approve_bill
from . import record_payment
from . import void_bill
from . import summary
from . import monthly
from . import prices
from . import return_goods

TABLE = "payables_requests"
ROUTES = {
    PayablesAction.SAVE_BILL: save_bill.handle,
    PayablesAction.APPROVE_BILL: approve_bill.handle,
    PayablesAction.RECORD_PAYMENT: record_payment.handle,
    PayablesAction.VOID_BILL: void_bill.handle,
    PayablesAction.SUMMARY: summary.handle,
    PayablesAction.MONTHLY: monthly.handle,
    PayablesAction.PRICES: prices.handle,
    PayablesAction.RETURN_GOODS: return_goods.handle,
}
handle = ActionDispatcher(ROUTES, PayablesAction, TABLE)
