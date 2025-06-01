from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.forecast_ml import forecast_next_week_balance
from app.services import model  

statement_analysis_bp = Blueprint("statement_analysis", __name__)

@statement_analysis_bp.route("/income_expense", methods=["POST"])
@jwt_required()
def income_expense():
    return model.expense_pie()

@statement_analysis_bp.route("/predict_next_week_balance", methods=["POST"])
@jwt_required()
def predict_next_week_balance():
    return forecast_next_week_balance()  

@statement_analysis_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze():
    return model.daily_income_expense_chart()
