
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from flask import send_file
from werkzeug.utils import secure_filename

from app.services.csv_service import export_transactions
from app.services.data_cleaning_service import import_and_clean_csv
from app.services.recurring_service import (
    get_all_recurring_expenses,
    add_recurring_expense,
    update_recurring_expense,
    delete_recurring_expense,
    process_due_recurring_expenses
)

from app.services.summary_service import get_monthly_summary
from app.repositories.transaction_repository import (
    get_all_transactions,
    get_transaction_by_id
)
from app.models import Category,Budget
from app.services.transaction_service import (
    add_transaction,
    delete_transaction,
    update_transaction
)
from app.services.budget_service import (
    set_monthly_budget,
    get_budget_status
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    today = datetime.today()

    summary = get_monthly_summary(today.year, today.month)

    transactions = get_all_transactions()[:5]

    categories = Category.query.order_by(
        Category.name
    ).all()

    budgets = Budget.query.filter_by(
        month=today.month,
        year=today.year
    ).all()

    budget_statuses = []

    for budget in budgets:
        status = get_budget_status(
            budget.category_id,
            today.month,
            today.year
        )

        budget_statuses.append({
            "category": budget.category.name,
            "budget": status["budget_paise"] / 100,
            "spent": status["spent_paise"] / 100,
            "remaining": status["remaining_paise"] / 100,
            "is_over_budget": status["is_over_budget"]
        })

    return render_template(
        "dashboard.html",
        summary=summary,
        transactions=transactions,
        categories=categories,
        budget_statuses=budget_statuses,
        today_month=today.month,
        today_year=today.year
    )

@dashboard_bp.route("/add-transaction", methods=["POST"])
def add_transaction_route():
    try:
        add_transaction(
            amount=request.form.get("amount"),
            transaction_type=request.form.get("transaction_type"),
            category_id=int(request.form.get("category_id")),
            description=request.form.get("description"),
            transaction_date=request.form.get("transaction_date")
        )

        flash("Transaction added successfully!", "success")
        return redirect(url_for("dashboard.dashboard"))

    except (ValueError, TypeError) as error:
        return str(error), 400


@dashboard_bp.route(
    "/delete-transaction/<int:transaction_id>",
    methods=["POST"]
)
def delete_transaction_route(transaction_id):
    try:
        delete_transaction(transaction_id)
        flash("Transaction deleted successfully!", "success")

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route(
    "/edit-transaction/<int:transaction_id>",
    methods=["GET", "POST"]
)
def edit_transaction_route(transaction_id):
    transaction = get_transaction_by_id(transaction_id)

    if transaction is None:
        return "Transaction not found", 404

    if request.method == "GET":
        return render_template(
            "edit_transaction.html",
            transaction=transaction,
            categories=Category.query.order_by(Category.name).all()
        )

    try:
        update_transaction(
            transaction_id=transaction_id,
            amount=request.form.get("amount"),
            transaction_type=request.form.get("transaction_type"),
            category_id=int(request.form.get("category_id")),
            description=request.form.get("description"),
            transaction_date=request.form.get("transaction_date")
        )

        flash("Transaction updated successfully!", "success")

    except (ValueError, TypeError) as error:
        flash(str(error), "error")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/set-budget", methods=["POST"])
def set_budget_route():
    try:
        set_monthly_budget(
            category_id=int(request.form.get("category_id")),
            amount=request.form.get("amount"),
            month=int(request.form.get("month")),
            year=int(request.form.get("year"))
        )

        flash("Monthly budget saved successfully!", "success")

    except (ValueError, TypeError) as error:
        flash(str(error), "error")

    return redirect(url_for("dashboard.dashboard"))

@dashboard_bp.route("/recurring-expenses")
def recurring_expenses_route():

    expenses = get_all_recurring_expenses(
        include_inactive=True
    )

    categories = Category.query.order_by(
        Category.name
    ).all()

    return render_template(
        "recurring_expenses.html",
        expenses=expenses,
        categories=categories
    )


@dashboard_bp.route("/add-recurring-expense", methods=["POST"])
def add_recurring_expense_route():

    try:
        add_recurring_expense(
            title=request.form.get("title"),
            amount=request.form.get("amount"),
            category_id=int(request.form.get("category_id")),
            frequency=request.form.get("frequency"),
            start_date=request.form.get("start_date")
        )

        flash("Recurring expense added successfully!", "success")

    except (ValueError, TypeError) as error:
        flash(str(error), "error")

    return redirect(url_for("dashboard.recurring_expenses_route"))


@dashboard_bp.route(
    "/update-recurring-expense/<int:expense_id>",
    methods=["POST"]
)
def update_recurring_expense_route(expense_id):

    try:
        update_recurring_expense(
            expense_id=expense_id,
            is_active=request.form.get("is_active") == "true"
        )

        flash("Recurring expense status updated!", "success")

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("dashboard.recurring_expenses_route"))


@dashboard_bp.route(
    "/delete-recurring-expense/<int:expense_id>",
    methods=["POST"]
)
def delete_recurring_expense_route(expense_id):

    try:
        delete_recurring_expense(expense_id)
        flash("Recurring expense deleted successfully!", "success")

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("dashboard.recurring_expenses_route"))

@dashboard_bp.route("/csv")
def csv_page():
    return render_template("csv_management.html")


@dashboard_bp.route("/export-csv")
def export_csv_route():
    try:
        export_path = os.path.join(
            os.getcwd(),
            "data",
            "transactions_export.csv"
        )

        os.makedirs(os.path.dirname(export_path), exist_ok=True)

        export_transactions(export_path)

        return send_file(
            export_path,
            as_attachment=True,
            download_name="transactions_export.csv",
            mimetype="text/csv"
        )

    except Exception as error:
        flash(f"CSV export failed: {error}", "error")
        return redirect(url_for("dashboard.csv_page"))


@dashboard_bp.route("/import-csv", methods=["POST"])
def import_csv_route():
    if "csv_file" not in request.files:
        flash("Please select a CSV file.", "error")
        return redirect(url_for("dashboard.csv_page"))

    file = request.files["csv_file"]

    if not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("dashboard.csv_page"))

    if not file.filename.lower().endswith(".csv"):
        flash("Only CSV files are allowed.", "error")
        return redirect(url_for("dashboard.csv_page"))

    try:
        filename = secure_filename(file.filename)

        upload_folder = os.path.join(
            os.getcwd(),
            "data",
            "uploads"
        )

        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename)

        file.save(file_path)

        report = import_and_clean_csv(file_path)
        flash(
            f"Processed {report['total_rows']} rows: {report['imported']} imported, "
            f"{report['duplicates']} duplicates skipped, {report['invalid']} invalid.",
            "success" if report["invalid"] == 0 else "warning"
        )
        for message in report["errors"][:10]:
            flash(message, "error")

    except (ValueError, OSError) as error:
        flash(f"CSV import failed: {error}", "error")

    return redirect(url_for("dashboard.csv_page"))


@dashboard_bp.route("/process-recurring", methods=["POST"])
def process_recurring_route():
    try:
        count = process_due_recurring_expenses()
        flash(f"Created {count} due recurring transaction(s).", "success")
    except (ValueError, TypeError) as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard.recurring_expenses_route"))
