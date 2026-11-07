from app import create_app
from app.models import Transaction
from app.utils.money import paise_to_rupees

app = create_app()

with app.app_context():

    transactions = Transaction.query.order_by(
        Transaction.id
    ).all()

    print("\nALL TRANSACTIONS")

    for transaction in transactions:
        amount = paise_to_rupees(transaction.amount_paise)

        print(
            transaction.id,
            transaction.transaction_type,
            f"₹{amount}",
            transaction.description
        )

    print("\nTotal transactions:", len(transactions))