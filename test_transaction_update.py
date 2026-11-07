from datetime import datetime

from app import create_app
from app.services.transaction_service import (
    update_transaction,
    add_transaction
)
from app.utils.money import paise_to_rupees
from app.services.transaction_service import delete_transaction
from app.models import Transaction
from app.extensions import db

app = create_app()

with app.app_context():

    # Create a test transaction
    transaction = add_transaction(
        amount="500.00",
        transaction_type="expense",
        category_id=1,
        description="Original Test Expense",
        transaction_date=datetime(2026, 11, 6, 10, 0)
    )

    print("Original Amount: ₹", paise_to_rupees(
        transaction.amount_paise
    ))

    # Update transaction
    updated = update_transaction(
        transaction_id=transaction.id,
        amount="750.00",
        description="Updated Test Expense"
    )

    print("\nTRANSACTION UPDATED")
    print("-------------------")
    print("Updated Amount: ₹", paise_to_rupees(
        updated.amount_paise
    ))
    print("Updated Description:", updated.description)
    
    # Delete transaction
    deleted = delete_transaction(transaction.id)

    print("\nTRANSACTION DELETED")
    print("-------------------")
    print("Deletion successful:", deleted)

    # Verify deletion
    deleted_record = db.session.get(
        Transaction,
        transaction.id
    )

    print("Deleted record found:", deleted_record is not None)    
    