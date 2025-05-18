from app import db
from datetime import datetime

class Goal(db.Model):
    __tablename__ = "core_goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("core_user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date)
    account_id = db.Column(db.Integer, db.ForeignKey("core_accounts.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "due_date": self.due_date.strftime("%Y-%m-%d") if self.due_date else None,
            "account_id": self.account_id
        }
