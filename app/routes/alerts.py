from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.budget import Budget
from app import db
from app.models.user import User
from app.utils.notifications import send_alert_email
alerts_bp = Blueprint("alerts", __name__)

@alerts_bp.route("/alerts/overspending", methods=["POST"])
@jwt_required()
def check_overspending():
    user_id = get_jwt_identity()

    # Fetch latest month budget
    latest_budget = (
        db.session.query(Budget)
        .filter_by(user_id=user_id)
        .order_by(Budget.month.desc())
        .first()
    )

    if not latest_budget:
        return jsonify({"message": "No budget found"}), 404

    overspent = [
        {
            "category": cat.name,
            "limit": cat.limit,
            "spent": cat.spent,
            "over_by": round(cat.spent - cat.limit, 2)
        }
        for cat in latest_budget.categories
        if cat.spent > cat.limit
    ]

    user = User.query.get(user_id)
    if overspent and user:
        send_alert_email(user.email, overspent)

    return jsonify({"overspent_categories": overspent}), 200
