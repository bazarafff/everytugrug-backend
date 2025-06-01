from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.goal import Goal
from app.models.transaction import Transaction
from datetime import datetime

goal_bp = Blueprint("goals", __name__)

@goal_bp.route("/goals/create", methods=["POST"])
@jwt_required()
def create_goal():
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get("name")
    target_amount = data.get("target_amount")
    due_date = data.get("due_date")
    account_id = data.get("account_id")

    goal = Goal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        due_date=datetime.strptime(due_date, "%Y-%m-%d") if due_date else None,
        account_id=account_id
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({"message": "Goal created", "goal": goal.to_dict()}), 201

@goal_bp.route("/goals", methods=["POST"])
@jwt_required()
def list_goals():
    user_id = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=user_id).all()
    return jsonify([g.to_dict() for g in goals])

@goal_bp.route("/goals/update/<int:goal_id>", methods=["POST"])
@jwt_required()
def update_goal(goal_id):
    user_id = get_jwt_identity()
    goal = Goal.query.get(goal_id)
    if not goal or goal.user_id != user_id:
        return jsonify({"error": "Goal not found"}), 404

    data = request.get_json()
    goal.current_amount = data.get("current_amount", goal.current_amount)
    db.session.commit()
    return jsonify({"message": "Goal updated", "goal": goal.to_dict()})
