
from datetime import date, timedelta
import calendar

from app.extensions import db
from app.models import RecurringExpense, Category
from app.utils.money import rupees_to_paise


def get_all_recurring_expenses(include_inactive=False):
    query = RecurringExpense.query

    if not include_inactive:
        query = query.filter_by(is_active=True)

    return query.order_by(
        RecurringExpense.next_due_date.asc()
    ).all()


def add_recurring_expense(
    title,
    amount,
    category_id,
    frequency,
    start_date
):
    if not title or not title.strip():
        raise ValueError("Title cannot be empty.")

    if frequency not in ("daily", "weekly", "monthly", "yearly"):
        raise ValueError("Invalid recurring frequency.")

    category = db.session.get(Category, category_id)

    if category is None:
        raise ValueError("Invalid category.")

    amount_paise = rupees_to_paise(amount)

    if isinstance(start_date, str):
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            raise ValueError("Invalid start date.")

    if not isinstance(start_date, date):
        raise ValueError("Start date must be a valid date.")

    expense = RecurringExpense(
        title=title.strip(),
        amount_paise=amount_paise,
        category_id=category_id,
        frequency=frequency,
        start_date=start_date,
        next_due_date=start_date,
        is_active=True
    )

    db.session.add(expense)
    db.session.commit()

    return expense


def calculate_next_due_date(current_date, frequency):

    if frequency == "daily":
        return current_date + timedelta(days=1)

    elif frequency == "weekly":
        return current_date + timedelta(weeks=1)

    elif frequency == "monthly":
        year = current_date.year
        month = current_date.month + 1

        if month > 12:
            month = 1
            year += 1

        last_day = calendar.monthrange(year, month)[1]
        day = min(current_date.day, last_day)

        return date(year, month, day)

    elif frequency == "yearly":
        try:
            return current_date.replace(
                year=current_date.year + 1
            )
        except ValueError:
            return current_date.replace(
                year=current_date.year + 1,
                day=28
            )

    raise ValueError("Invalid recurring frequency.")


def update_recurring_expense(
    expense_id,
    title=None,
    amount=None,
    frequency=None,
    is_active=None
):
    expense = db.session.get(RecurringExpense, expense_id)

    if expense is None:
        raise ValueError("Recurring expense not found.")

    if title is not None:
        if not title.strip():
            raise ValueError("Title cannot be empty.")

        expense.title = title.strip()

    if amount is not None:
        expense.amount_paise = rupees_to_paise(amount)

    if frequency is not None:
        if frequency not in ("daily", "weekly", "monthly", "yearly"):
            raise ValueError("Invalid recurring frequency.")

        expense.frequency = frequency

    if is_active is not None:
        expense.is_active = is_active

    db.session.commit()

    return expense


def delete_recurring_expense(expense_id):
    expense = db.session.get(RecurringExpense, expense_id)

    if expense is None:
        raise ValueError("Recurring expense not found.")

    db.session.delete(expense)
    db.session.commit()

    return True


def process_due_recurring_expenses(today=None):
    """Create each due expense once and advance its schedule atomically."""
    from datetime import datetime
    from app.models import Transaction
    today = today or date.today()
    if isinstance(today, datetime):
        today = today.date()
    if not isinstance(today, date):
        raise ValueError("Today must be a date.")
    due_items = RecurringExpense.query.filter(
        RecurringExpense.is_active.is_(True),
        RecurringExpense.next_due_date <= today
    ).order_by(RecurringExpense.id).all()
    created = 0
    try:
        for item in due_items:
            while item.next_due_date <= today:
                due_date = item.next_due_date
                db.session.add(Transaction(
                    amount_paise=item.amount_paise,
                    transaction_type="expense",
                    description=f"Recurring: {item.title}",
                    transaction_date=datetime.combine(due_date, datetime.min.time()),
                    category_id=item.category_id
                ))
                item.next_due_date = calculate_next_due_date(due_date, item.frequency)
                created += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return created
