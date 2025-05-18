# app/models/recurring.py

from app import db
from datetime import datetime

class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_txn'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('core_user.id'))
    amount = db.Column(db.Float)
    txn_type = db.Column(db.String(10))  # 'in' or 'out'
    remarks = db.Column(db.String(255))
    recurrence = db.Column(db.String(20))  # 'monthly', 'weekly'
    next_due_date = db.Column(db.Date)
