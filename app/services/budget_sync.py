from app.models.budget import BudgetCategory
from app.models.transaction import Transaction
from app import db

def sync_budget_category_spent(user_id, budget_id):
    categories = BudgetCategory.query.filter_by(budget_id=budget_id).all()
    for category in categories:
        total_spent = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.remarks.ilike(f"%{category.name}%")
        ).scalar() or 0.0
        category.spent = abs(total_spent)
    db.session.commit()
