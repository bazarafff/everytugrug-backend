from datetime import datetime
from app import db

class Transaction(db.Model):
    __tablename__ = "core_txn" 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("core_user.id"), nullable=False)
    txn_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    txn_type = db.Column(db.String(10))  # 'in' or 'out'
    remarks = db.Column(db.String(255))
    bank = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
