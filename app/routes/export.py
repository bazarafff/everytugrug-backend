from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.budget import Budget, BudgetCategory
from app.models.goal import Goal
import csv
import io

export_bp = Blueprint("export", __name__)

def generate_csv(data, fieldnames):
    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    return si.getvalue()

@export_bp.route("/export/transactions", methods=["POST"])
@jwt_required()
def export_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    data = [{
        "txn_date": t.txn_date,
        "amount": t.amount,
        "txn_type": t.txn_type,
        "remarks": t.remarks,
        "bank": t.bank
    } for t in transactions]
    csv_data = generate_csv(data, ["txn_date", "amount", "txn_type", "remarks", "bank"])
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=transactions.csv"}
    )

@export_bp.route("/export/budgets", methods=["POST"])
@jwt_required()
def export_budgets():
    user_id = get_jwt_identity()
    budgets = Budget.query.filter_by(user_id=user_id).all()
    data = [{
        "month": b.month,
        "total_income": b.total_income,
        "total_expense": b.total_expense
    } for b in budgets]
    csv_data = generate_csv(data, ["month", "total_income", "total_expense"])
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=budgets.csv"}
    )

@export_bp.route("/export/goals", methods=["POST"])
@jwt_required()
def export_goals():
    user_id = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=user_id).all()
    data = [{
        "name": g.name,
        "target_amount": g.target_amount,
        "current_amount": g.current_amount,
        "due_date": g.due_date,
        "account_id": g.account_id
    } for g in goals]
    csv_data = generate_csv(data, ["name", "target_amount", "current_amount", "due_date", "account_id"])
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=goals.csv"}
    )
