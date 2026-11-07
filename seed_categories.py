from app import create_app
from app.extensions import db
from app.models import Category

app = create_app()

default_categories = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Healthcare",
    "Entertainment",
    "Bills",
    "Rent",
    "Other"
]

with app.app_context():

    for category_name in default_categories:

        existing_category = Category.query.filter_by(
            name=category_name
        ).first()

        if existing_category is None:

            category = Category(name=category_name)

            db.session.add(category)

    db.session.commit()

    print("Default categories added successfully!")