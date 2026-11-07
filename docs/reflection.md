# Project Reflection

This project demonstrates a modular Flask application with a SQLAlchemy data layer, service-level business rules, a browser interface, and automated tests. Amounts are stored as integer paise to avoid binary floating-point currency errors. CSV ingestion separates valid, duplicate, and invalid records so one malformed row does not discard the entire import. Dates with explicit offsets are normalized to Asia/Kolkata before they are stored; naive dates from the form are treated as India local time.

The main learning outcomes are separating routes from business logic, validating untrusted data, designing idempotent imports, handling calendar boundaries, writing regression tests, and using coverage and CI to protect future changes. Further production work should add authentication, CSRF protection, database migrations for deployed schema changes, and a production WSGI server.
