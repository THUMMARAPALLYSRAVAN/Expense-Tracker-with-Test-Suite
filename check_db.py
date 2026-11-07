from app import create_app
from app.models import Category

app = create_app()

with app.app_context():

    categories = Category.query.all()

    print("\nAvailable Expense Categories:")

    for category in categories:
        print(f"{category.id}. {category.name}")

    print(f"\nTotal Categories: {len(categories)}")