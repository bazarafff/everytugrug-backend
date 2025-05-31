import os
from flask import current_app, request, jsonify
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db

UPLOAD_FOLDER = "uploads/profile_pics"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/upload-profile-pic', methods=['POST'])
@jwt_required()
def upload_profile_pic():
    # 🔐 Хэрэглэгчийн ID авах
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Хэрэглэгч олдсонгүй."}), 404

    # 📂 Файл шалгах
    if 'file' not in request.files:
        return jsonify({"error": "Файл олдсонгүй."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл сонгогдоогүй байна."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Файлын формат зөвшөөрөгдөөгүй байна. Зөвшөөрөгдөх формат: png, jpg, jpeg."}), 400

    # 📁 Зураг хадгалах
    filename = secure_filename(file.filename)
    os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER), exist_ok=True)
    save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, f"{user_id}_{filename}")
    file.save(save_path)

    # 🔗 DB-д зурагны зам хадгалах (жишээ нь: /uploads/profile_pics/1_filename.jpg)
    user.profile_picture = f"/{UPLOAD_FOLDER}/{user_id}_{filename}"
    db.session.commit()

    return jsonify({
        "message": "Зураг амжилттай байршууллаа.",
        "profile_picture": user.profile_picture
    }), 200
