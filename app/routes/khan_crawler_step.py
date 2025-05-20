from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.khanbank_worker.task import Task
from app.services.khanbank_worker.worker import KhanbankWorker
from queue import Queue
from threading import Thread
import uuid

khan_crawler_step_bp = Blueprint("khan_crawler_step", __name__)

# Shared state
task_queue = Queue()
results = {}

# Start background worker
worker = KhanbankWorker(task_queue, results)
Thread(target=worker.run, daemon=True).start()

@khan_crawler_step_bp.route("/crawl/start", methods=["POST"])
@jwt_required()
def start_login():
    data = request.get_json()
    user_id = get_jwt_identity()
    username = data.get("username")
    password = data.get("password")

    session_id = str(uuid.uuid4())
    task = Task(session_id=session_id, username=username, password=password, step="start")
    task_queue.put(task)
    results[session_id] = {"status": "processing", "user_id": user_id}
    return jsonify({"success": True, "session_id": session_id})

@khan_crawler_step_bp.route("/crawl/verify", methods=["POST"])
@jwt_required()
def verify_otp():
    data = request.get_json()
    session_id = data.get("session_id")
    otp_code = data.get("otp_code")

    if session_id not in results:
        return jsonify({"error": "Session not found"}), 404

    task = Task(session_id=session_id, otp_code=otp_code, step="verify")
    task_queue.put(task)
    results[session_id]["status"] = "verifying"
    return jsonify({"success": True, "message": "OTP submitted"})

@khan_crawler_step_bp.route("/crawl/status", methods=["POST"])
@jwt_required()
def crawl_status():
    data = request.get_json()
    session_id = data.get("session_id")
    result = results.get(session_id)

    if not result:
        return jsonify({"success": False, "error": "Invalid session"}), 404

    return jsonify({"success": True, **result})
