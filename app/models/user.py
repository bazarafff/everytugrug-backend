from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "core_user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # ✅ New fields
    phone_number = db.Column(db.String(20))
    profile_picture = db.Column(db.String(255))  # Can store S3/Render CDN URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Relationships
    transactions = db.relationship('Transaction', back_populates='user', cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
