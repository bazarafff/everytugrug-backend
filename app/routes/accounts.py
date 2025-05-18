from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.account import Account

account_bp = Blueprint("accounts", __name__)

@account_bp.route("/accounts", methods=["POST"])
@jwt_required()
def create_account():
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get("name")
    account_type = data.get("account_type", "bank")
    balance = data.get("balance", 0.0)

    account = Account(user_id=user_id, name=name, account_type=account_type, balance=balance)
    db.session.add(account)
    db.session.commit()

    return jsonify({"message": "Account created", "account": account.to_dict()}), 201

@account_bp.route("/accounts", methods=["POST"])
@jwt_required()
def get_accounts():
    user_id = get_jwt_identity()
    accounts = Account.query.filter_by(user_id=user_id).all()
    return jsonify([a.to_dict() for a in accounts])
