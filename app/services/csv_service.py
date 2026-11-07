import csv

from app.extensions import db
from app.models import Category, Transaction
from app.repositories.transaction_repository import get_all_transactions
from app.utils.dates import normalize_datetime
from app.utils.money import paise_to_rupees, rupees_to_paise


def export_transactions(file_path):
    transactions = get_all_transactions()
    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Amount", "Type", "Description", "Date", "Category"])
        for transaction in transactions:
            writer.writerow([
                transaction.id,
                format(paise_to_rupees(transaction.amount_paise), ".2f"),
                transaction.transaction_type,
                transaction.description,
                transaction.transaction_date.isoformat(),
                transaction.category.name,
            ])
    return len(transactions)


def import_transactions(file_path):
    """Import clean exported CSV data; skip only exact duplicate records."""
    imported_count = 0
    required = {"Amount", "Type", "Description", "Date", "Category"}
    try:
        with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError("CSV is missing required columns.")
            for row_number, row in enumerate(reader, start=2):
                for column in required:
                    if not row.get(column) or not row[column].strip():
                        raise ValueError(f"Row {row_number}: Missing required CSV field: {column}")
                amount_paise = rupees_to_paise(row["Amount"])
                transaction_type = row["Type"].strip().lower()
                if transaction_type not in ("income", "expense"):
                    raise ValueError(f"Row {row_number}: Invalid transaction type.")
                description = row["Description"].strip()
                if not description or len(description) > 200:
                    raise ValueError(f"Row {row_number}: Invalid description.")
                transaction_date = normalize_datetime(row["Date"])
                category = Category.query.filter_by(name=row["Category"].strip()).first()
                if category is None:
                    raise ValueError(f"Row {row_number}: Unknown category: {row['Category']}")
                values = dict(amount_paise=amount_paise, transaction_type=transaction_type,
                              description=description, transaction_date=transaction_date,
                              category_id=category.id)
                if Transaction.query.filter_by(**values).first():
                    continue
                db.session.add(Transaction(**values))
                db.session.flush()
                imported_count += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return imported_count
