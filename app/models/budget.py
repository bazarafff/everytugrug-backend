# app/models/budget.py
from app import db
from datetime import datetime

class Budget(db.Model):
    __tablename__ = 'core_budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('core_user.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    total_income = db.Column(db.Float, default=0.0)
    total_expense = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    categories = db.relationship(
        'BudgetCategory',
        backref='budget',
        lazy=True,
        cascade="all, delete"
    )


class BudgetCategory(db.Model):
    __tablename__ = 'core_budget_categories'

    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('core_budgets.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    total_limit = db.Column(db.Float, nullable=False)
    spent = db.Column(db.Float, default=0.0)

    def remaining(self):
        
        return self.total_limit - self.spent
