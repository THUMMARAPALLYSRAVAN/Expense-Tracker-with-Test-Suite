
from app.utils.dates import month_bounds
from sqlalchemy import func

from app.extensions import db
from app.models import Budget, Category, Transaction
from app.utils.money import rupees_to_paise


def set_monthly_budget(category_id, amount, month, year):
    if not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")

    if not isinstance(year, int) or year < 1:
        raise ValueError("Invalid year.")

    category = db.session.get(Category, category_id)

    if category is None:
        raise ValueError("Invalid category.")

    amount_paise = rupees_to_paise(amount)

    budget = Budget.query.filter_by(
        category_id=category_id,
        month=month,
        year=year
    ).first()

    if budget:
        budget.amount_paise = amount_paise
    else:
        budget = Budget(
            category_id=category_id,
            amount_paise=amount_paise,
            month=month,
            year=year
        )
        db.session.add(budget)

    db.session.commit()
    return budget


def get_monthly_budget(category_id, month, year):
    return Budget.query.filter_by(
        category_id=category_id,
        month=month,
        year=year
    ).first()


def get_budget_status(category_id, month, year):
    budget = get_monthly_budget(category_id, month, year)

    if budget is None:
        raise ValueError("Budget not found.")

    start_date, end_date = month_bounds(year, month)

    spent = db.session.query(
        func.coalesce(func.sum(Transaction.amount_paise), 0)
    ).filter(
        Transaction.category_id == category_id,
        Transaction.transaction_type == "expense",
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date
    ).scalar()

    remaining = budget.amount_paise - spent

    return {
        "budget_paise": budget.amount_paise,
        "spent_paise": spent,
        "remaining_paise": remaining,
        "is_over_budget": spent > budget.amount_paise
    }
