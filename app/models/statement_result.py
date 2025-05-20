from app import db
from datetime import datetime

class StatementResult(db.Model):
    __tablename__ = 'statement_result'

    id = db.Column(db.Integer, primary_key=True)
    txn_date = db.Column(db.DateTime, nullable=False)
    begin_balance = db.Column(db.Numeric, nullable=True)
    debit = db.Column(db.Numeric, nullable=True)
    credit = db.Column(db.Numeric, nullable=True)
    end_balance = db.Column(db.Numeric, nullable=True)
    description = db.Column(db.Text, nullable=True)
    counterparty = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional: Link to authenticated user
    user_id = db.Column(db.Integer, nullable=True)  # Set via access token

    def __repr__(self):
        return f"<Statement txn_date={self.txn_date} debit={self.debit} credit={self.credit}>"
