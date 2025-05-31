# app/routes/budget.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.budget import Budget, BudgetCategory
from app.models.transaction import Transaction
from datetime import datetime
from app.services.budget_sync import sync_budget_category_spent

budget_bp = Blueprint("budget", __name__)

@budget_bp.route("/", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = get_jwt_identity()
    data = request.get_json()
    month = data.get("month")  # Format: "2025-05"
    total_income = data.get("totalIncome", 0.0)
    total_expense = data.get("totalExpense", 0.0)

    if not month:
        return jsonify({"error": "Сар заавал байх ёстой"}), 400

    if Budget.query.filter_by(user_id=user_id, month=month).first():
        return jsonify({"error": "Энэ сард төсөв бүртгэгдсэн байна"}), 409

    budget = Budget(
        user_id=user_id,
        month=month,
        total_income=total_income,
        total_expense=total_expense
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify({"message": "Төсөв амжилттай үүсгэгдлээ", "id": budget.id}), 201


@budget_bp.route("/get/<month>", methods=["POST"])
@jwt_required()
def get_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Төсөв олдсонгүй"}), 404

    categories = BudgetCategory.query.filter_by(budget_id=budget.id).all()
    return jsonify({
        "month": budget.month,
        "totalIncome": budget.total_income,
        "totalExpense": budget.total_expense,
        "categories": [
            {
                "name": c.name,
                "totalLimit": c.total_limit,
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
        return jsonify({"error": "Төсөв олдсонгүй"}), 404

    if "totalIncome" in data:
        budget.total_income = data["totalIncome"]
    if "totalExpense" in data:
        budget.total_expense = data["totalExpense"]

    db.session.commit()
    return jsonify({"message": "Төсөв шинэчлэгдлээ"})


@budget_bp.route("/<month>/category", methods=["POST"])
@jwt_required()
def add_budget_category(month):
    user_id = get_jwt_identity()
    data = request.get_json()
    category_name = data.get("categoryName")
    total_limit = data.get("totalLimit")

    if not category_name or total_limit is None:
        return jsonify({"error": "Ангиллын нэр болон хязгаар заавал байх ёстой"}), 400

    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Төсөв олдсонгүй"}), 404

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
    return jsonify({"message": "Ангилал амжилттай нэмэгдлээ/шинэчлэгдлээ"})


@budget_bp.route("/<month>/track", methods=["POST"])
@jwt_required()
def track_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Төсөв олдсонгүй"}), 404

    categories = BudgetCategory.query.filter_by(budget_id=budget.id).all()
    tracked_data = [
        {
            "category": c.name,
            "totalLimit": c.total_limit,
            "spent": c.spent,
            "remaining": c.remaining(),
            "isOver": c.spent > c.total_limit
        } for c in categories
    ]
    is_budget_over = any(c["isOver"] for c in tracked_data)

    return jsonify({
        "month": budget.month,
        "totalIncome": budget.total_income,
        "totalExpense": budget.total_expense,
        "isBudgetOver": is_budget_over,
        "tracked": tracked_data
    })


@budget_bp.route("/<month>/check", methods=["POST"])
@jwt_required()
def check_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Төсөв олдсонгүй"}), 404

    # Тухайн сарын нийт зардлыг Transaction table-с авах
    total_spent = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.txn_date.between(f"{month}-01", f"{month}-31"),
        Transaction.amount < 0
    ).scalar() or 0.0

    is_over = abs(total_spent) > budget.total_expense

    return jsonify({
        "month": month,
        "budgetLimit": budget.total_expense,
        "totalSpent": abs(total_spent),
        "isOver": is_over,
        "message": f"Таны сарын нийт зардал {abs(total_spent)}₮. {('Хэтэрсэн байна!' if is_over else 'Хэтрээгүй байна.')}"
    })



@budget_bp.route("/<month>/track", methods=["POST"])
@jwt_required()
def track_budget(month):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        return jsonify({"error": "Төсөв олдсонгүй"}), 404

    sync_budget_category_spent(user_id, budget.id)

    # 📝 tracked_data-гаа гаргана
