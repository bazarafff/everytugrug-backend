from flask import Blueprint, jsonify, request, Response, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from weasyprint import HTML

export_bp = Blueprint("export", __name__)

# PDF генератор функц
def generate_pdf(data, title, fieldnames):
    html_template = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h2>{{ title }}</h2>
        <table>
            <thead>
                <tr>
                    {% for field in fieldnames %}
                    <th>{{ field }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in data %}
                <tr>
                    {% for field in fieldnames %}
                    <td>{{ row[field] }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    rendered_html = render_template_string(html_template, title=title, data=data, fieldnames=fieldnames)
    pdf_file = HTML(string=rendered_html).write_pdf()
    return pdf_file

# Transactions PDF Export
@export_bp.route("/export/transactions/pdf", methods=["POST"])
@jwt_required()
def export_transactions_pdf():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    data = [{
        "txn_date": t.txn_date,
        "amount": t.amount,
        "txn_type": t.txn_type,
        "remarks": t.remarks,
        "bank": t.bank
    } for t in transactions]
    pdf_data = generate_pdf(data, "Transactions", ["txn_date", "amount", "txn_type", "remarks", "bank"])
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=transactions.pdf"}
    )

# Budgets PDF Export
@export_bp.route("/export/budgets/pdf", methods=["POST"])
@jwt_required()
def export_budgets_pdf():
    user_id = get_jwt_identity()
    budgets = Budget.query.filter_by(user_id=user_id).all()
    data = [{
        "month": b.month,
        "total_income": b.total_income,
        "total_expense": b.total_expense
    } for b in budgets]
    pdf_data = generate_pdf(data, "Budgets", ["month", "total_income", "total_expense"])
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=budgets.pdf"}
    )

# Goals PDF Export
@export_bp.route("/export/goals/pdf", methods=["POST"])
@jwt_required()
def export_goals_pdf():
    user_id = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=user_id).all()
    data = [{
        "name": g.name,
        "target_amount": g.target_amount,
        "current_amount": g.current_amount,
        "due_date": g.due_date,
        "account_id": g.account_id
    } for g in goals]
    pdf_data = generate_pdf(data, "Goals", ["name", "target_amount", "current_amount", "due_date", "account_id"])
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=goals.pdf"}
    )
