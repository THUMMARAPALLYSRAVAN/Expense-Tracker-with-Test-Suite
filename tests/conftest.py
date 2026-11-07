import pytest
from app import create_app
from app.extensions import db
from app.models import Category


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        for name in ["Food", "Travel", "Bills", "Salary", "Other"]:
            db.session.add(Category(name=name))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def category_id(app):
    with app.app_context():
        return Category.query.filter_by(name="Food").one().id
