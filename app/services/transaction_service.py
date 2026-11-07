from app.extensions import db
from app.models import Transaction, Category
from app.utils.money import rupees_to_paise
from app.utils.dates import normalize_datetime


def add_transaction(amount, transaction_type, category_id, description, transaction_date):
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Description cannot be empty.")
    description = description.strip()
    if len(description) > 200:
        raise ValueError("Description cannot exceed 200 characters.")
    if transaction_type not in ("income", "expense"):
        raise ValueError("Type must be income or expense.")
    category = db.session.get(Category, category_id)
    if category is None:
        raise ValueError("Invalid category selected.")
    amount_paise = rupees_to_paise(amount)
    normalized_date = normalize_datetime(transaction_date)
    transaction = Transaction(amount_paise=amount_paise, transaction_type=transaction_type,
                              category_id=category_id, description=description,
                              transaction_date=normalized_date)
    try:
        db.session.add(transaction)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return transaction


def update_transaction(transaction_id, amount=None, transaction_type=None, category_id=None, description=None, transaction_date=None):
    transaction = db.session.get(Transaction, transaction_id)
    if transaction is None:
        raise ValueError("Transaction not found.")
    if amount is not None:
        transaction.amount_paise = rupees_to_paise(amount)
    if transaction_type is not None:
        if transaction_type not in ("income", "expense"):
            raise ValueError("Invalid transaction type.")
        transaction.transaction_type = transaction_type
    if category_id is not None:
        if db.session.get(Category, category_id) is None:
            raise ValueError("Invalid category.")
        transaction.category_id = category_id
    if description is not None:
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Description cannot be empty.")
        if len(description.strip()) > 200:
            raise ValueError("Description cannot exceed 200 characters.")
        transaction.description = description.strip()
    if transaction_date is not None:
        transaction.transaction_date = normalize_datetime(transaction_date)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return transaction


def delete_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if transaction is None:
        raise ValueError("Transaction not found.")
    db.session.delete(transaction)
    db.session.commit()
    return True
