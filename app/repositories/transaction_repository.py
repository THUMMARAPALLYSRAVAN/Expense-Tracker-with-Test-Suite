from app.models import Transaction
from app.extensions import db


def get_all_transactions():
    return Transaction.query.order_by(
        Transaction.id.desc()
    ).all()

def get_transaction_by_id(transaction_id):
    return db.session.get(Transaction, transaction_id)


def get_transactions_by_type(transaction_type):
    return Transaction.query.filter_by(
        transaction_type=transaction_type
    ).order_by(
        Transaction.transaction_date.desc()
    ).all()