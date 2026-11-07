from app import create_app
from app.services.csv_service import export_transactions
from app.services.csv_service import import_transactions

app = create_app()

with app.app_context():

    count = export_transactions("data/transactions_export.csv")

    print("CSV EXPORT SUCCESSFUL")
    print("---------------------")
    print("Transactions exported:", count)
    print("File: data/transactions_export.csv")
    imported_count = import_transactions(
        "data/transactions_export.csv"
    )

    print("\nCSV IMPORT SUCCESSFUL")
    print("---------------------")
    print("Transactions imported:", imported_count)    