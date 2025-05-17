# app/routes/summary.py

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import extract, func
from app.models.transaction import Transaction
from app import db

summary_bp = Blueprint("summary", __name__)

@summary_bp.route("/summary/monthly", methods=["GET"])
@jwt_required()
def monthly_summary():
    user_id = get_jwt_identity()

    results = db.session.query(
        extract('year', Transaction.txn_date).label("year"),
        extract('month', Transaction.txn_date).label("month"),
        func.sum(func.case([(Transaction.txn_type == "in", Transaction.amount)], else_=0)).label("total_income"),
        func.sum(func.case([(Transaction.txn_type == "out", Transaction.amount)], else_=0)).label("total_expense")
    ).filter(Transaction.user_id == user_id).group_by("year", "month").order_by("year", "month").all()

    summary = [
        {
            "year": int(r.year),
            "month": int(r.month),
            "total_income": float(r.total_income or 0),
            "total_expense": float(r.total_expense or 0),
            "net": float((r.total_income or 0) - (r.total_expense or 0))
        }
        for r in results
    ]

    return jsonify(summary)
