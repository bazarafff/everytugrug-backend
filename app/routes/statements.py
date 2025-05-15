# app/routes/statements.py

from flask import Blueprint

stmt_bp = Blueprint("statements", __name__)

@stmt_bp.route("/ping", methods=["GET"])
def ping():
    return {"message": "Statement route is alive!"}
