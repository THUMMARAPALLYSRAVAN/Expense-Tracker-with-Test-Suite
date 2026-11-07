import csv
from datetime import datetime
from decimal import InvalidOperation

from app.extensions import db
from app.models import Category, Transaction
from app.utils.money import rupees_to_paise
from app.utils.dates import normalize_datetime


def parse_transaction_date(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Transaction date is missing.")
    value = value.strip()
    try:
        return normalize_datetime(value)
    except ValueError:
        pass
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y")
    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    raise ValueError("Unsupported date format.")


def clean_transaction_row(row):
    required = ("Amount", "Type", "Description", "Date", "Category")
    for field in required:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing required field: {field}")
    transaction_type = row["Type"].strip().lower()
    if transaction_type not in ("income", "expense"):
        raise ValueError("Invalid transaction type.")
    description = row["Description"].strip()
    if len(description) > 200:
        raise ValueError("Description cannot exceed 200 characters.")
    amount_paise = rupees_to_paise(row["Amount"].strip())
    transaction_date = parse_transaction_date(row["Date"])
    category_name = row["Category"].strip()
    category = Category.query.filter_by(name=category_name).first()
    if category is None:
        raise ValueError(f"Unknown category: {category_name}")
    return {"amount_paise": amount_paise, "transaction_type": transaction_type,
            "description": description, "transaction_date": transaction_date,
            "category_id": category.id}


def import_and_clean_csv(file_path):
    report = {"total_rows": 0, "imported": 0, "duplicates": 0, "invalid": 0, "errors": []}
    try:
        with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            required = {"Amount", "Type", "Description", "Date", "Category"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError("CSV is missing required columns.")
            for row_number, row in enumerate(reader, start=2):
                report["total_rows"] += 1
                try:
                    cleaned = clean_transaction_row(row)
                    duplicate = Transaction.query.filter_by(**cleaned).first()
                    if duplicate:
                        report["duplicates"] += 1
                        continue
                    db.session.add(Transaction(**cleaned))
                    db.session.flush()
                    report["imported"] += 1
                except (ValueError, TypeError, KeyError, InvalidOperation) as error:
                    report["invalid"] += 1
                    report["errors"].append(f"Row {row_number}: {error}")
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return report
