# Expense Tracker with Test Suite

A Flask + SQLAlchemy personal finance application for recording income and expenses, setting category budgets, managing recurring expenses, and importing/exporting CSV data.

## Features

- Income and expense CRUD with category selection and validation.
- Currency stored as integer paise; Decimal half-up rounding avoids float errors.
- Monthly income, expense, and balance summaries.
- Category/month budgets with spent, remaining, and over-budget status.
- Recurring expense schedules (daily, weekly, monthly, yearly), including month-end/leap-year calculations. Use **Process Due Expenses** on the recurring page to create all due transactions; this action is explicit and idempotent.
- CSV export and import. Import supports ISO dates, `DD-MM-YYYY`, `MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY/MM/DD`, and `DD-Mon-YYYY`; slash dates are interpreted month/day first because the supplied dirty-data generator emits `MM/DD/YYYY`.
- Dirty-data cleaner reports imported, duplicate, and invalid rows rather than aborting on a bad record.
- Pytest regression suite, coverage configuration, Ruff lint workflow, and GitHub Actions CI.

## Requirements

- Python 3.11+
- Windows / macOS / Linux

## Run on Windows PowerShell

Open PowerShell in the project directory:

```powershell
# Activate your existing environment
.\venv\Scripts\Activate.ps1

# Install dependencies if required
python -m pip install -r requirements.txt

# Create tables and seed categories (only needed on a fresh database)
python create_db.py
python seed_categories.py

# Start the application
python run.py
```

Open `http://127.0.0.1:5000/` in your browser. The SQLite database is stored under Flask's `instance` directory. Do not delete it if you want to preserve your existing records.

## Generate and clean the 1,000-row sample file

```powershell
python generate_sample_data.py
```

Then open **CSV Management**, upload `data/dirty_transactions.csv`, and review the summary. The importer skips exact duplicates and invalid rows, while preserving valid rows.

## Run automated tests and coverage

```powershell
python -m pip install pytest pytest-cov ruff
ruff check app tests --select E4,E7,E9,F
pytest --cov=app --cov-report=term-missing --cov-report=html
```

Open `htmlcov\index.html` to inspect the coverage report. The target for the internship is at least 30 tests and more than 80% coverage; use the actual local report as the final evidence rather than assuming a target has been met.

## Project structure

```text
ExpenseTracker/
├── app/
│   ├── models.py
│   ├── repositories/
│   ├── routes/
│   ├── services/
│   ├── static/
│   ├── templates/
│   └── utils/
├── data/
├── docs/
├── tests/
├── .github/workflows/tests.yml
├── create_db.py
├── seed_categories.py
├── generate_sample_data.py
├── requirements.txt
└── run.py
```

## Date and timezone policy

SQLite `DateTime` columns are stored as naive Asia/Kolkata wall time. Naive values submitted by the HTML form are interpreted as India local time. Offset-aware CSV/API values are converted to Asia/Kolkata before storage. Monthly reports use inclusive start and exclusive next-month boundaries, preventing last-day/first-day off-by-one errors.

## Before production deployment

This is an educational prototype. Add authentication/authorization, CSRF protection, database migrations, secure production secrets, and a production WSGI server before exposing it to the public internet.
