from app import create_app
from app.services.budget_service import (
    set_monthly_budget,
    get_monthly_budget
)
from app.utils.money import paise_to_rupees
from app.services.budget_service import get_budget_status
app = create_app()

with app.app_context():

    budget = set_monthly_budget(
        category_id=1,
        amount="5000.00",
        month=11,
        year=2026
    )

    print("MONTHLY BUDGET CREATED")
    print("Category:", budget.category.name)
    print("Budget: ₹", paise_to_rupees(budget.amount_paise))

    # Retrieve existing budget
    retrieved_budget = get_monthly_budget(
        category_id=1,
        month=11,
        year=2026
    )

    if retrieved_budget:
        print("\nBUDGET RETRIEVED SUCCESSFULLY")
        print("Category:", retrieved_budget.category.name)
        print("Budget: ₹", paise_to_rupees(
            retrieved_budget.amount_paise
        ))
    else:
        print("Budget not found.")
        
    # Check budget status
    status = get_budget_status(
        category_id=1,
        month=11,
        year=2026
    )

    print("\nMONTHLY BUDGET STATUS")
    print("---------------------")

    print(
        "Total Budget: ₹",
        paise_to_rupees(status["budget_paise"])
    )

    print(
        "Total Spent: ₹",
        paise_to_rupees(status["spent_paise"])
    )

    print(
        "Remaining: ₹",
        paise_to_rupees(status["remaining_paise"])
    )

    print("Over Budget:", status["is_over_budget"])        