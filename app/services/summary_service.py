from sqlalchemy import func
from app.extensions import db
from app.models import Transaction
from app.utils.dates import month_bounds


def get_monthly_summary(year, month):
    start_date, end_date = month_bounds(year, month)
    results = db.session.query(
        Transaction.transaction_type,
        func.coalesce(func.sum(Transaction.amount_paise), 0)
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date
    ).group_by(Transaction.transaction_type).all()
    totals = {"income": 0, "expense": 0}
    for transaction_type, amount in results:
        if transaction_type in totals:
            totals[transaction_type] = int(amount or 0)
    return {"year": year, "month": month,
            "total_income_paise": totals["income"],
            "total_expense_paise": totals["expense"],
            "balance_paise": totals["income"] - totals["expense"]}
