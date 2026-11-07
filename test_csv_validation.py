from app import create_app
from app.services.csv_service import import_transactions

app = create_app()

with app.app_context():
    try:
        import_transactions("data/invalid_transactions.csv")
    except ValueError as error:
        print("CSV VALIDATION PASSED:", error)