from datetime import datetime

from app import create_app
from app.services.transaction_service import add_transaction

app = create_app()

with app.app_context():

    try:
        add_transaction(
            amount="100",
            transaction_type="expense",
            category_id=1,
            description="",
            transaction_date=datetime(2026, 11, 6)
        )

    except ValueError as error:
        print("VALIDATION PASSED:", error)