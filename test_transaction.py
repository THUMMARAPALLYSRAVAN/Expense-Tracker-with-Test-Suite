from datetime import datetime

from app import create_app
from app.services.transaction_service import add_transaction
from app.utils.money import paise_to_rupees

app = create_app()

with app.app_context():

    # Add expense
    expense = add_transaction(
        amount="250.50",
        transaction_type="expense",
        category_id=1,
        description="Lunch",
        transaction_date=datetime(2026, 11, 6, 12, 0)
    )

    print("Expense added successfully!")
    print("Amount: ₹", paise_to_rupees(expense.amount_paise))

    # Add income
    income = add_transaction(
        amount="15000.00",
        transaction_type="income",
        category_id=1,
        description="Freelance Payment",
        transaction_date=datetime(2026, 11, 6, 13, 0)
    )

    print("\nIncome added successfully!")
    print("Amount: ₹", paise_to_rupees(income.amount_paise))