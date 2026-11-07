from app import create_app
from app.models import Transaction

app = create_app()

with app.app_context():
    transactions = Transaction.query.filter_by(
        description="Test Expense"
    ).all()

    print("Matching transactions:", len(transactions))

    for transaction in transactions:
        print(
            transaction.description,
            transaction.amount_paise,
            transaction.transaction_type
        )