from app import create_app
from app.repositories.transaction_repository import get_all_transactions

app = create_app()

with app.app_context():

    transactions = get_all_transactions()

    print("Total transactions:", len(transactions))

    for transaction in transactions:
        print(
            transaction.id,
            transaction.transaction_type,
            transaction.amount_paise,
            transaction.description
        )