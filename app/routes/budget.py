from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.budget import Budget, BudgetCategory
from datetime import datetime

budget_bp = Blueprint("budget", __name__)

@budget_bp.route("/", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = get_jwt_identity()
    data = request.get_json()
    month = data.get("month")  # Format: "2025-05"
    total_income = data.get("total_income", 0.0)
    total_expense = data.get("total_expense", 0.0)

    if not month:
        return jsonify({"error": "Month is required"}), 400

    if Budget.query.filter_by(user_id=user_id, month=month).first():
        return jsonify({"error": "Budget already exists for this month"}), 409

    budget = Budget(
        user_id=user_id,
        month=month,
        total_income=total_income,
        total_expense=total_expense
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify({"message": "Budget created", "id": budget.id}), 201


@budget_bp.route("/get/<month>", methods=["POST"])
@jwt_required()
def get_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    categories = BudgetCategory.query.filter_by(budget_id=budget.id).all()
    return jsonify({
        "month": budget.month,
        "total_income": budget.total_income,
        "total_expense": budget.total_expense,
        "categories": [
            {
                "name": c.name,
                "total_limit": c.total_limit,
                "spent": c.spent,
                "remaining": c.remaining()
            } for c in categories
        ]
    })


@budget_bp.route("/update/<month>", methods=["POST"])
@jwt_required()
def update_budget(month):
    user_id = get_jwt_identity()
    data = request.get_json()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    if "total_income" in data:
        budget.total_income = data["total_income"]
    if "total_expense" in data:
        budget.total_expense = data["total_expense"]

    db.session.commit()
    return jsonify({"message": "Budget updated"})


@budget_bp.route("/<month>/category", methods=["POST"])
@jwt_required()
def add_budget_category(month):
    user_id = get_jwt_identity()
    data = request.get_json()
    category_name = data.get("category_name")
    total_limit = data.get("total_limit")

    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    category = BudgetCategory.query.filter_by(budget_id=budget.id, name=category_name).first()
    if category:
        category.total_limit = total_limit
    else:
        category = BudgetCategory(
            budget_id=budget.id,
            name=category_name,
            total_limit=total_limit
        )
        db.session.add(category)

    db.session.commit()
    return jsonify({"message": "Category added/updated"})


@budget_bp.route("/<month>/track", methods=["POST"])
@jwt_required()
def track_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    categories = BudgetCategory.query.filter_by(budget_id=budget.id).all()
    tracked_data = [
        {
            "category": c.name,
            "total_limit": c.total_limit,
            "spent": c.spent,
            "remaining": c.remaining()
        } for c in categories
    ]

    return jsonify({
        "month": budget.month,
        "total_income": budget.total_income,
        "total_expense": budget.total_expense,
        "tracked": tracked_data
    })
