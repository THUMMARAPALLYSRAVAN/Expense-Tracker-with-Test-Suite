from app import create_app
from app.services.recurring_service import get_all_recurring_expenses
from app.utils.money import paise_to_rupees
from app.services.recurring_service import add_recurring_expense
from app.services.recurring_service import update_recurring_expense

from app.services.recurring_service import calculate_next_due_date
from datetime import date
from app.services.recurring_service import delete_recurring_expense
from app.extensions import db


app = create_app()

with app.app_context():

    expenses = get_all_recurring_expenses()

    print("\nACTIVE RECURRING EXPENSES")
    print("-------------------------")

    print("Total recurring expenses:", len(expenses))

    for expense in expenses:
        print("Title:", expense.title)
        print("Amount: ₹", paise_to_rupees(expense.amount_paise))
        print("Frequency:", expense.frequency)
        print("Next Due Date:", expense.next_due_date)
        
    # Add a recurring expense
    expense = add_recurring_expense(
        title="Monthly Internet Bill",
        amount="799.00",
        category_id=7,
        frequency="monthly",
        start_date="2026-11-10"
    )

    print("\nRECURRING EXPENSE CREATED")
    print("-------------------------")
    print("Title:", expense.title)
    print("Amount: ₹", paise_to_rupees(expense.amount_paise))
    print("Frequency:", expense.frequency)
    print("Start Date:", expense.start_date)
    print("Next Due Date:", expense.next_due_date)
    
    print("\nNEXT DUE DATE CALCULATIONS")
    print("--------------------------")

    monthly = calculate_next_due_date(
        date(2026, 11, 10), "monthly"
    )

    weekly = calculate_next_due_date(
        date(2026, 11, 10), "weekly"
    )

    yearly = calculate_next_due_date(
        date(2026, 11, 10), "yearly"
    )

    print("Monthly:", monthly)
    print("Weekly:", weekly)
    print("Yearly:", yearly)       
    
    print("\nMONTH-END DATE TESTS")
    print("--------------------")

    february = calculate_next_due_date(
        date(2027, 1, 31), "monthly"
    )

    leap_february = calculate_next_due_date(
        date(2028, 1, 31), "monthly"
    )

    leap_year = calculate_next_due_date(
        date(2028, 2, 29), "yearly"
    )

    print("January 31 -> February:", february)
    print("Leap February:", leap_february)
    print("Leap year -> Next year:", leap_year)   
    
    
    # Update recurring expense
    updated_expense = update_recurring_expense(
        expense_id=expense.id,
        title="Updated Internet Bill",
        amount="999.00",
        frequency="monthly"
    )

    print("\nRECURRING EXPENSE UPDATED")
    print("-------------------------")
    print("Title:", updated_expense.title)
    print("Amount: ₹", paise_to_rupees(updated_expense.amount_paise))
    print("Frequency:", updated_expense.frequency)  
    
    
    # Delete recurring expense
    deleted = delete_recurring_expense(expense.id)

    print("\nRECURRING EXPENSE DELETED")
    print("-------------------------")
    print("Deletion successful:", deleted)

    # Verify deletion
    remaining = get_all_recurring_expenses()

    print("Remaining active recurring expenses:", len(remaining))   
    
    from app.models import RecurringExpense

    deleted_record = db.session.get(
        RecurringExpense,
        expense.id
    )

    print("Deleted record found:", deleted_record is not None)    
         
        
        