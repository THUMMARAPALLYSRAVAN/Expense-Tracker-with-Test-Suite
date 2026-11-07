import csv
import random
from datetime import date, timedelta

random.seed(42)

categories = [
    "Food", "Travel", "Shopping", "Education",
    "Healthcare", "Entertainment", "Bills", "Rent", "Other"
]

transactions = []
start_date = date(2026, 1, 1)

for i in range(1000):
    transaction_date = start_date + timedelta(
        days=random.randint(0, 300)
    )

    amount = round(random.uniform(50, 10000), 2)

    row = [
        amount,
        random.choice(["income", "expense"]),
        f"Transaction {i + 1}",
        transaction_date.isoformat(),
        random.choice(categories)
    ]

    # Add duplicate records
    if i > 0 and i % 20 == 0:
        row = random.choice(transactions).copy()

    # Add invalid amounts
    if i % 50 == 0:
        row[0] = random.choice(["abc", "", "-100", "NaN"])

    # Add mixed date formats
    if i % 3 == 0:
        row[3] = transaction_date.strftime("%d-%m-%Y")
    elif i % 3 == 1:
        row[3] = transaction_date.strftime("%m/%d/%Y")

    transactions.append(row)

with open(
    "data/dirty_transactions.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:
    writer = csv.writer(file)
    writer.writerow([
        "Amount", "Type", "Description", "Date", "Category"
    ])
    writer.writerows(transactions)

print("Sample CSV generated successfully!")
print("Total transactions:", len(transactions))
print("File: data/dirty_transactions.csv")