# app/routes/statement_analysis.py
from flask import Blueprint, request, jsonify, send_file
from app.services import model  # assuming you refactor functions into model.py

statement_analysis_bp = Blueprint("statement_analysis", __name__)

@statement_analysis_bp.route("/income_expense", methods=["POST"])
def income_expense():
    return model.expense_pie()

@statement_analysis_bp.route("/predict_next_week_balance", methods=["POST"])
def predict_next_week_balance():
    return model.forecast_plot()

@statement_analysis_bp.route("/analyze", methods=["POST"])
def analyze():
    return model.analyze_financial_data()
