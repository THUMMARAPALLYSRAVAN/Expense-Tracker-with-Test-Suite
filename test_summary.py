from app import create_app
from app.services.summary_service import get_monthly_summary
from app.utils.money import paise_to_rupees

app = create_app()

with app.app_context():

    summary = get_monthly_summary(2026, 11)

    print("\nMONTHLY FINANCIAL SUMMARY")
    print("-------------------------")

    print(
        "Total Income: ₹",
        paise_to_rupees(summary["total_income_paise"])
    )

    print(
        "Total Expenses: ₹",
        paise_to_rupees(summary["total_expense_paise"])
    )

    print(
        "Remaining Balance: ₹",
        paise_to_rupees(summary["balance_paise"])
    )