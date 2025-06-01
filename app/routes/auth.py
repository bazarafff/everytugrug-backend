import base64
import os
from flask import Blueprint, current_app, request, jsonify
from app import db
from app.models.user import User
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
import re

from werkzeug.utils import secure_filename

auth_bp = Blueprint("auth", __name__)

def is_strong_password(password):
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', password))

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    phone_number = data.get("phone_number")

    if not all([username, email, password, phone_number]):
        return jsonify({"error": "Мэдээлэл дутуу байна."}), 400

    if not is_strong_password(password):
        return jsonify({"error": "Нууц үг сул байна. Том жижиг үсэг, тоо, тусгай тэмдэгт оролцсон, 8-аас дээш тэмдэгттэй байх шаардлагатай."}), 400

    if User.query.filter((User.username == username) | (User.email == email) | (User.phone_number == phone_number)).first():
        return jsonify({"error": "Хэрэглэгчийн нэр, и-мэйл эсвэл утасны дугаар аль нэг нь бүртгэлтэй байна."}), 409

    user = User(username=username, email=email, phone_number=phone_number)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "message": "Бүртгэл амжилттай."}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get("identifier")  # username, email, эсвэл phone_number
    password = data.get("password")

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier) | (User.phone_number == identifier)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Нэвтрэх мэдээлэл буруу байна."}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token}), 200

# 📌 JWT ашиглан хэрэглэгчийн мэдээлэл авах (POST болгосон)
@auth_bp.route('/me', methods=['POST'])
@jwt_required()
def me():
    if not request.is_json:
        return jsonify({"error": "Content-Type: application/json байх шаардлагатай."}), 415

    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Хэрэглэгч олдсонгүй."}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "profile_picture": user.profile_picture,
        "created_at": user.created_at.isoformat()
    })


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    identifier = data.get("identifier")  # email эсвэл phone_number
    new_password = data.get("new_password")

    if not all([identifier, new_password]):
        return jsonify({"error": "Мэдээлэл дутуу байна."}), 400

    user = User.query.filter((User.email == identifier) | (User.phone_number == identifier)).first()
    if not user:
        return jsonify({"error": "Хэрэглэгч олдсонгүй."}), 404

    if not is_strong_password(new_password):
        return jsonify({"error": "Нууц үг сул байна. Том жижиг үсэг, тоо, тусгай тэмдэгт оролцсон, 8-аас дээш тэмдэгттэй байх шаардлагатай."}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Нууц үг амжилттай шинэчлэгдлээ."}), 200




UPLOAD_FOLDER = "uploads/profile_pics"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/upload-profile-pic', methods=['POST'])
@jwt_required()
def upload_profile_pic():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Хэрэглэгч олдсонгүй."}), 404

    # ✅ Content-Type шалгах
    if not request.is_json:
        return jsonify({"error": "Content-Type: application/json байх шаардлагатай."}), 415

    data = request.get_json()
    base64_str = data.get("profile_picture")
    if not base64_str:
        return jsonify({"error": "profile_picture талбар шаардлагатай."}), 400

    # (Сонголт) Base64 формат шалгах
    try:
        base64.b64decode(base64_str)
    except Exception:
        return jsonify({"error": "Base64 string буруу байна."}), 400

    # 🔗 DB-д хадгалах
    user.profile_picture = base64_str
    db.session.commit()

    return jsonify({
        "message": "Зураг амжилттай хадгаллаа.",
        "profile_picture": user.profile_picture  
    }), 200
