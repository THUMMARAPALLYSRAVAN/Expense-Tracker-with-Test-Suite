from datetime import date, datetime, timezone
from decimal import Decimal
import csv

import pytest

from app.extensions import db
from app.models import Budget, RecurringExpense, Transaction
from app.utils.money import rupees_to_paise, paise_to_rupees
from app.utils.dates import normalize_datetime, month_bounds
from app.services.transaction_service import add_transaction, update_transaction, delete_transaction
from app.services.summary_service import get_monthly_summary
from app.services.budget_service import set_monthly_budget, get_budget_status
from app.services.recurring_service import (
    add_recurring_expense, calculate_next_due_date,
    process_due_recurring_expenses, get_all_recurring_expenses,
    update_recurring_expense, delete_recurring_expense,
)
from app.services.csv_service import export_transactions, import_transactions
from app.services.data_cleaning_service import (
    parse_transaction_date, clean_transaction_row, import_and_clean_csv,
)
from app.repositories.transaction_repository import get_all_transactions, get_transaction_by_id, get_transactions_by_type


def test_money_round_trip():
    assert paise_to_rupees(12345) == Decimal("123.45")

@pytest.mark.parametrize("amount, expected", [("1", 100), ("1.2", 120), ("1.234", 123), ("1.235", 124), ("0.01", 1), ("999999.99", 99999999)])
def test_rupees_to_paise_rounding(amount, expected):
    assert rupees_to_paise(amount) == expected

@pytest.mark.parametrize("amount", [None, True, "", "abc", "NaN", "Infinity", "-1", "0", "0.00"])
def test_invalid_money(amount):
    with pytest.raises(ValueError):
        rupees_to_paise(amount)

@pytest.mark.parametrize("month", [0, 13, -1, True])
def test_invalid_month(month):
    with pytest.raises(ValueError):
        month_bounds(2026, month)

@pytest.mark.parametrize("year", [0, -1, 9999, True])
def test_invalid_year(year):
    with pytest.raises(ValueError):
        month_bounds(year, 1)

@pytest.mark.parametrize("month, expected_end", [(1, datetime(2026, 2, 1)), (11, datetime(2026, 12, 1)), (12, datetime(2027, 1, 1))])
def test_month_bounds(month, expected_end):
    assert month_bounds(2026, month) == (datetime(2026, month, 1), expected_end)


def test_aware_datetime_normalized_to_india():
    utc_value = datetime(2026, 1, 31, 20, 0, tzinfo=timezone.utc)
    assert normalize_datetime(utc_value) == datetime(2026, 2, 1, 1, 30)


def test_naive_datetime_preserved():
    value = datetime(2026, 11, 7, 9, 15)
    assert normalize_datetime(value) == value


def test_add_transaction(app, category_id):
    with app.app_context():
        item = add_transaction("99.99", "expense", category_id, "Lunch", "2026-11-07")
        assert item.amount_paise == 9999
        assert item.description == "Lunch"

@pytest.mark.parametrize("kind", ["transfer", "EXPENSE", ""])
def test_add_transaction_rejects_type(app, category_id, kind):
    with app.app_context(), pytest.raises(ValueError):
        add_transaction("10", kind, category_id, "x", datetime(2026, 1, 1))

@pytest.mark.parametrize("description", [None, "", "   "])
def test_add_transaction_rejects_description(app, category_id, description):
    with app.app_context(), pytest.raises(ValueError):
        add_transaction("10", "expense", category_id, description, datetime(2026, 1, 1))


def test_add_transaction_rejects_bad_category(app):
    with app.app_context(), pytest.raises(ValueError):
        add_transaction("10", "expense", 999, "x", datetime(2026, 1, 1))


def test_add_transaction_rejects_bad_date(app, category_id):
    with app.app_context(), pytest.raises(ValueError):
        add_transaction("10", "expense", category_id, "x", "not-a-date")


def test_update_transaction(app, category_id):
    with app.app_context():
        item = add_transaction("10", "expense", category_id, "Old", datetime(2026, 1, 1))
        changed = update_transaction(item.id, amount="20.50", description="New")
        assert changed.amount_paise == 2050 and changed.description == "New"


def test_update_missing_transaction(app):
    with app.app_context(), pytest.raises(ValueError):
        update_transaction(100)


def test_delete_transaction(app, category_id):
    with app.app_context():
        item = add_transaction("10", "expense", category_id, "Delete", datetime(2026, 1, 1))
        assert delete_transaction(item.id) is True
        assert get_transaction_by_id(item.id) is None


def test_delete_missing_transaction(app):
    with app.app_context(), pytest.raises(ValueError):
        delete_transaction(123)


def test_repository_filters_and_order(app, category_id):
    with app.app_context():
        a = add_transaction("10", "expense", category_id, "A", datetime(2026, 1, 1))
        b = add_transaction("20", "income", category_id, "B", datetime(2026, 1, 2))
        assert get_all_transactions()[0].id == b.id
        assert get_transaction_by_id(a.id).description == "A"
        assert [x.description for x in get_transactions_by_type("income")] == ["B"]


def test_monthly_summary_and_exclusive_boundary(app, category_id):
    with app.app_context():
        add_transaction("100", "income", category_id, "Jan last", datetime(2026, 1, 31, 23, 59))
        add_transaction("20", "expense", category_id, "Feb first", datetime(2026, 2, 1, 0, 0))
        summary = get_monthly_summary(2026, 1)
        assert summary["total_income_paise"] == 10000
        assert summary["total_expense_paise"] == 0


def test_empty_month_summary(app):
    with app.app_context():
        summary = get_monthly_summary(2026, 3)
        assert summary["balance_paise"] == 0


def test_budget_create_and_status(app, category_id):
    with app.app_context():
        set_monthly_budget(category_id, "100", 11, 2026)
        add_transaction("30", "expense", category_id, "Food", datetime(2026, 11, 5))
        status = get_budget_status(category_id, 11, 2026)
        assert status["spent_paise"] == 3000
        assert status["remaining_paise"] == 7000
        assert not status["is_over_budget"]


def test_budget_upsert(app, category_id):
    with app.app_context():
        first = set_monthly_budget(category_id, "100", 11, 2026)
        second = set_monthly_budget(category_id, "200", 11, 2026)
        assert first.id == second.id and second.amount_paise == 20000
        assert Budget.query.count() == 1


def test_budget_over_limit(app, category_id):
    with app.app_context():
        set_monthly_budget(category_id, "10", 11, 2026)
        add_transaction("12", "expense", category_id, "Over", datetime(2026, 11, 5))
        assert get_budget_status(category_id, 11, 2026)["is_over_budget"]


def test_budget_missing(app, category_id):
    with app.app_context(), pytest.raises(ValueError):
        get_budget_status(category_id, 11, 2026)


@pytest.mark.parametrize("frequency, start, expected", [
    ("daily", date(2026, 1, 1), date(2026, 1, 2)),
    ("weekly", date(2026, 1, 1), date(2026, 1, 8)),
    ("monthly", date(2026, 1, 31), date(2026, 2, 28)),
    ("monthly", date(2028, 1, 31), date(2028, 2, 29)),
    ("yearly", date(2028, 2, 29), date(2029, 2, 28)),
])
def test_next_due_date(frequency, start, expected):
    assert calculate_next_due_date(start, frequency) == expected


def test_recurring_add_update_delete(app, category_id):
    with app.app_context():
        item = add_recurring_expense("Internet", "799", category_id, "monthly", "2026-11-01")
        assert item.next_due_date == date(2026, 11, 1)
        update_recurring_expense(item.id, title="WiFi", is_active=False)
        assert item.title == "WiFi" and not item.is_active
        assert delete_recurring_expense(item.id)
        assert RecurringExpense.query.count() == 0


def test_recurring_invalid_frequency(app, category_id):
    with app.app_context(), pytest.raises(ValueError):
        add_recurring_expense("X", "10", category_id, "hourly", date(2026, 1, 1))


def test_recurring_due_processing_is_idempotent(app, category_id):
    with app.app_context():
        item = add_recurring_expense("Rent", "500", category_id, "monthly", date(2026, 10, 1))
        count = process_due_recurring_expenses(date(2026, 11, 15))
        assert count == 2
        assert Transaction.query.filter(Transaction.description == "Recurring: Rent").count() == 2
        assert item.next_due_date == date(2026, 12, 1)
        assert process_due_recurring_expenses(date(2026, 11, 15)) == 0


def test_get_recurring_inactive_option(app, category_id):
    with app.app_context():
        item = add_recurring_expense("Cloud", "50", category_id, "weekly", date(2026, 12, 1))
        update_recurring_expense(item.id, is_active=False)
        assert get_all_recurring_expenses() == []
        assert len(get_all_recurring_expenses(include_inactive=True)) == 1


@pytest.mark.parametrize("value, expected", [
    ("2026-11-07", datetime(2026, 11, 7)),
    ("07-11-2026", datetime(2026, 11, 7)),
    ("11/07/2026", datetime(2026, 11, 7)),
    ("2026/11/07", datetime(2026, 11, 7)),
    ("07-Nov-2026", datetime(2026, 11, 7)),
])
def test_parse_supported_dates(value, expected):
    assert parse_transaction_date(value) == expected

@pytest.mark.parametrize("value", ["", "nonsense", "32-13-2026"])
def test_parse_invalid_dates(value):
    with pytest.raises(ValueError):
        parse_transaction_date(value)


def test_clean_csv_row(app, category_id):
    with app.app_context():
        row = {"Amount": "25.50", "Type": "EXPENSE", "Description": "Tea", "Date": "07-11-2026", "Category": "Food"}
        cleaned = clean_transaction_row(row)
        assert cleaned["amount_paise"] == 2550
        assert cleaned["transaction_type"] == "expense"
        assert cleaned["category_id"] == category_id


def test_import_csv_reports_invalid_and_duplicate(app, category_id, tmp_path):
    with app.app_context():
        path = tmp_path / "mixed.csv"
        rows = [
            ["10.00", "expense", "Tea", "2026-11-07", "Food"],
            ["10.00", "expense", "Tea", "2026-11-07", "Food"],
            ["NaN", "expense", "Bad", "2026-11-07", "Food"],
            ["20", "income", "Salary", "07-11-2026", "Salary"],
        ]
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Amount", "Type", "Description", "Date", "Category"])
            writer.writerows(rows)
        report = import_and_clean_csv(path)
        assert report["total_rows"] == 4
        assert report["imported"] == 2
        assert report["duplicates"] == 1
        assert report["invalid"] == 1


def test_import_rejects_missing_columns(app, tmp_path):
    with app.app_context():
        path = tmp_path / "bad.csv"
        path.write_text("Amount,Type\n1,expense\n", encoding="utf-8")
        with pytest.raises(ValueError):
            import_and_clean_csv(path)


def test_dashboard_get(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Expense Tracker" in response.data


def test_csv_page_get(client):
    assert client.get("/csv").status_code == 200


def test_recurring_page_get(client):
    assert client.get("/recurring-expenses").status_code == 200


def test_add_transaction_route(client, category_id):
    response = client.post("/add-transaction", data={
        "amount": "35.50", "transaction_type": "expense",
        "category_id": str(category_id), "description": "Coffee",
        "transaction_date": "2026-11-07"
    })
    assert response.status_code == 302


def test_add_transaction_route_invalid(client, category_id):
    response = client.post("/add-transaction", data={
        "amount": "-1", "transaction_type": "expense",
        "category_id": str(category_id), "description": "Coffee",
        "transaction_date": "2026-11-07"
    })
    assert response.status_code == 400


def test_csv_export_and_exact_round_trip(app, category_id, tmp_path):
    with app.app_context():
        add_transaction("18.25", "expense", category_id, "Round trip", datetime(2026, 11, 7, 10, 30))
        path = tmp_path / "export.csv"
        assert export_transactions(path) == 1
        assert import_transactions(path) == 0
        assert Transaction.query.count() == 1


def test_csv_import_preserves_distinct_records_with_same_description(app, category_id, tmp_path):
    with app.app_context():
        path = tmp_path / "two.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Amount", "Type", "Description", "Date", "Category"])
            writer.writerow(["10", "expense", "Same", "2026-11-07", "Food"])
            writer.writerow(["20", "expense", "Same", "2026-11-07", "Food"])
        assert import_transactions(path) == 2


def test_budget_route(client, category_id):
    response = client.post("/set-budget", data={
        "category_id": str(category_id), "amount": "500", "month": "11", "year": "2026"
    })
    assert response.status_code == 302


def test_recurring_add_route(client, category_id):
    response = client.post("/add-recurring-expense", data={
        "title": "Internet", "amount": "500", "category_id": str(category_id),
        "frequency": "monthly", "start_date": "2026-11-01"
    })
    assert response.status_code == 302


def test_recurring_processing_route(client):
    response = client.post("/process-recurring")
    assert response.status_code == 302


def test_edit_missing_transaction_route(client):
    assert client.get("/edit-transaction/999").status_code == 404


def test_export_route(client):
    response = client.get("/export-csv")
    assert response.status_code == 200
    assert b"Amount" in response.data
    

def test_add_transaction_rejects_long_description(app, category_id):
    with app.app_context():
        with pytest.raises(ValueError, match="200 characters"):
            add_transaction(
                "100",
                "expense",
                category_id,
                "A" * 201,
                datetime(2026, 11, 7)
            )


def test_update_transaction_rejects_invalid_type(app, category_id):
    with app.app_context():
        item = add_transaction(
            "100", "expense", category_id,
            "Test", datetime(2026, 11, 7)
        )

        with pytest.raises(ValueError, match="Invalid transaction type"):
            update_transaction(item.id, transaction_type="transfer")


def test_update_transaction_rejects_invalid_category(app, category_id):
    with app.app_context():
        item = add_transaction(
            "100", "expense", category_id,
            "Test", datetime(2026, 11, 7)
        )

        with pytest.raises(ValueError, match="Invalid category"):
            update_transaction(item.id, category_id=999)


def test_update_transaction_rejects_long_description(app, category_id):
    with app.app_context():
        item = add_transaction(
            "100", "expense", category_id,
            "Test", datetime(2026, 11, 7)
        )

        with pytest.raises(ValueError, match="200 characters"):
            update_transaction(item.id, description="A" * 201)
    
