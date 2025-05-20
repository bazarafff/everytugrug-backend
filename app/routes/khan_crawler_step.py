from flask import Blueprint, request, jsonify
from app.services.statement_session import start_login_session, submit_otp
from flask_jwt_extended import jwt_required, get_jwt_identity

khan_crawler_step_bp = Blueprint("khan_crawler_step", __name__)

# app/routes/khan_crawler_step.py
@khan_crawler_step_bp.route("/crawl/start", methods=["POST"])
@jwt_required()
def start_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    user_id = get_jwt_identity()

    try:
        session_id = start_login_session(username, password, user_id)
        return jsonify({"status": "otp_required", "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@khan_crawler_step_bp.route("/crawl/verify", methods=["POST"])
@jwt_required()
def verify_otp():
    data = request.json
    session_id = data.get("session_id")
    otp = data.get("otp")

    try:
        result = submit_otp(session_id, otp)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
