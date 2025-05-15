import base64
import fitz  # PyMuPDF
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app import db
from app.models.transaction import Transaction

stmt_bp = Blueprint("statements", __name__)

@stmt_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_statement():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Read PDF content
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()

    # Parse the text (replace with your logic)
    lines = text.splitlines()
    transactions = []

    for line in lines:
        # Dummy example: parse lines like "2024-05-01 | 50000 | in | ATM withdrawal"
        parts = line.split('|')
        if len(parts) != 4:
            continue
        try:
            txn_date = datetime.strptime(parts[0].strip(), "%Y-%m-%d").date()
            amount = float(parts[1].strip())
            txn_type = parts[2].strip().lower()
            remarks = parts[3].strip()
        except Exception:
            continue

        txn = Transaction(
            user_id=user_id,
            txn_date=txn_date,
            amount=amount,
            txn_type=txn_type,
            remarks=remarks,
            bank="Khan Bank"  # or detect based on file
        )
        transactions.append(txn)

    db.session.add_all(transactions)
    db.session.commit()

    return jsonify({"message": f"{len(transactions)} transactions uploaded."}), 201

@stmt_bp.route('/crawl', methods=['POST'])
@jwt_required()
def crawl_khan_statement():
    user_id = get_jwt_identity()
    data = request.get_json()

    username = data.get("username")
    encoded_password = data.get("password")
    account = data.get("account_no")
    bank = data.get("bank", "KHAN")  # default Khan

    if not all([username, encoded_password, account]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        decoded_password = base64.b64decode(encoded_password).decode("utf-8")
    except Exception:
        return jsonify({"error": "Invalid password encoding"}), 400

    payload = {
        "username": username,
        "password": decoded_password,
        "account": account,
        "bank": bank,
        "from_date": "2024-01-01",
        "to_date": "2024-06-01"
    }

    try:
        res = requests.post("http://localhost:8000/api/scoring/bank", json=payload)
        res.raise_for_status()
        transactions = res.json().get("data", [])
    except Exception as e:
        return jsonify({"error": "Failed to fetch statement", "details": str(e)}), 500

    inserted = 0
    for txn in transactions:
        try:
            txn_date = datetime.strptime(txn["transactionDate"], "%Y-%m-%d").date()
            amount = float(txn["amount"]["amount"])
            txn_type = "in" if txn["amountType"]["codeDescription"] == "Credit" else "out"
            remarks = txn.get("transactionRemarks", "")

            new_txn = Transaction(
                user_id=user_id,
                txn_date=txn_date,
                amount=amount,
                txn_type=txn_type,
                remarks=remarks,
                bank="KHAN"
            )
            db.session.add(new_txn)
            inserted += 1
        except Exception as e:
            continue

    db.session.commit()
    return jsonify({"message": f"{inserted} transactions inserted."}), 201



@stmt_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_user_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.txn_date.desc()).all()

    return jsonify([
        {
            "date": t.txn_date.strftime("%Y-%m-%d"),
            "amount": t.amount,
            "type": t.txn_type,
            "remarks": t.remarks,
            "bank": t.bank
        } for t in transactions
    ])


@stmt_bp.route('/transactions', methods=['GET'])
@jwt_required()
def list_transactions():
    user_id = get_jwt_identity()
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    txn_type = request.args.get("type")  # 'in' or 'out'
    bank = request.args.get("bank")      # e.g., 'KHAN'

    query = Transaction.query.filter_by(user_id=user_id)

    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            query = query.filter(Transaction.txn_date >= from_dt)
        except ValueError:
            return jsonify({"error": "Invalid 'from' date format. Use YYYY-MM-DD."}), 400

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            query = query.filter(Transaction.txn_date <= to_dt)
        except ValueError:
            return jsonify({"error": "Invalid 'to' date format. Use YYYY-MM-DD."}), 400

    if txn_type:
        query = query.filter(Transaction.txn_type == txn_type)

    if bank:
        query = query.filter(Transaction.bank.ilike(bank))

    transactions = query.order_by(Transaction.txn_date.desc()).all()

    return jsonify([
        {
            "date": t.txn_date.strftime("%Y-%m-%d"),
            "amount": t.amount,
            "type": t.txn_type,
            "remarks": t.remarks,
            "bank": t.bank
        } for t in transactions
    ])