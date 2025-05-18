from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.budget import Budget, BudgetCategory
from datetime import datetime

budget_bp = Blueprint("budget", __name__)

@budget_bp.route("/budget", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = get_jwt_identity()
    data = request.get_json()
    month = data.get("month")  # Format: "2025-05"
    total_limit = data.get("total_limit")

    if not (month and total_limit):
        return jsonify({"error": "month and total_limit are required"}), 400

    if Budget.query.filter_by(user_id=user_id, month=month).first():
        return jsonify({"error": "Budget already exists for this month"}), 409

    budget = Budget(user_id=user_id, month=month, total_limit=total_limit)
    db.session.add(budget)
    db.session.commit()
    return jsonify({"message": "Budget created", "id": budget.id}), 201

@budget_bp.route("/budget/get/<month>", methods=["POST"])
@jwt_required()
def get_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    categories = BudgetCategory.query.filter_by(budget_id=budget.id).all()
    return jsonify({
        "month": budget.month,
        "total_limit": budget.total_limit,
        "categories": [
            {"name": c.category_name, "limit": c.limit} for c in categories
        ]
    })

@budget_bp.route("/budget/update/<month>", methods=["POST"])
@jwt_required()
def update_budget(month):
    user_id = get_jwt_identity()
    data = request.get_json()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    if "total_limit" in data:
        budget.total_limit = data["total_limit"]
    db.session.commit()
    return jsonify({"message": "Budget updated"})

@budget_bp.route("/budget/<month>/category", methods=["POST"])
@jwt_required()
def add_budget_category(month):
    user_id = get_jwt_identity()
    data = request.get_json()
    category_name = data.get("category_name")
    limit = data.get("limit")

    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    category = BudgetCategory.query.filter_by(budget_id=budget.id, category_name=category_name).first()
    if category:
        category.limit = limit
    else:
        category = BudgetCategory(budget_id=budget.id, category_name=category_name, limit=limit)
        db.session.add(category)
    db.session.commit()
    return jsonify({"message": "Category added/updated"})

@budget_bp.route("/budget/<month>/track", methods=["POST"])
@jwt_required()
def track_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    categories = BudgetCategory.query.filter_by(budget_id=budget.id).all()

    # Future extension: match spending from transactions by category
    tracked_data = [
        {
            "category": c.category_name,
            "limit": c.limit,
            "spent": 0  # Placeholder
        }
        for c in categories
    ]
    return jsonify({
        "month": month,
        "total_limit": budget.total_limit,
        "tracked": tracked_data
    })
