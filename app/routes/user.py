from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db

user_bp = Blueprint("user", __name__)

@user_bp.route("/update_profile", methods=["POST"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Хэрэглэгч олдсонгүй"}), 404

    data = request.get_json()
    if "email" in data:
        user.email = data["email"]
    if "phone_number" in data:
        user.phone_number = data["phone_number"]
    if "username" in data:
        user.username = data["username"]
    db.session.commit()
    return jsonify({"message": "Хувийн мэдээлэл шинэчлэгдлээ.", "user": {
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number
    }})
