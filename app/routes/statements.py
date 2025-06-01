import base64
import fitz  # PyMuPDF
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from sqlalchemy import extract, func
from app import db
from app.models.transaction import Transaction
import csv
from io import StringIO
from flask import Response
import pandas as pd
import os
from werkzeug.utils import secure_filename

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
    bank = data.get("bank", "KHAN")  

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
                bank = txn.get("bank", "KHAN")

            )
            db.session.add(new_txn)
            inserted += 1
        except Exception as e:
            continue

    db.session.commit()
    return jsonify({"message": f"{inserted} transactions inserted."}), 201



@stmt_bp.route('/transactions/user', methods=['POST'])
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


@stmt_bp.route('/transactions/all', methods=['POST'])
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

@stmt_bp.route('/summary', methods=['POST'])
@jwt_required()
def get_summary():
    user_id = get_jwt_identity()

    summary = (
        db.session.query(
            extract('year', Transaction.txn_date).label('year'),
            extract('month', Transaction.txn_date).label('month'),
            func.sum(
                func.case((Transaction.txn_type == 'in', Transaction.amount), else_=0)
            ).label('income'),
            func.sum(
                func.case((Transaction.txn_type == 'out', Transaction.amount), else_=0)
            ).label('expense')
        )
        .filter(Transaction.user_id == user_id)
        .group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )

    result = []
    for row in summary:
        result.append({
            "year": int(row.year),
            "month": int(row.month),
            "income": float(row.income),
            "expense": float(row.expense),
            "net": float(row.income - row.expense)
        })

    return jsonify(result)


@stmt_bp.route('/export', methods=['POST'])
@jwt_required()
def export_csv():
    user_id = get_jwt_identity()
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    txn_type = request.args.get("type")
    bank = request.args.get("bank")

    query = Transaction.query.filter_by(user_id=user_id)

    if from_date:
        query = query.filter(Transaction.txn_date >= from_date)
    if to_date:
        query = query.filter(Transaction.txn_date <= to_date)
    if txn_type:
        query = query.filter(Transaction.txn_type == txn_type)
    if bank:
        query = query.filter(Transaction.bank.ilike(bank))

    transactions = query.order_by(Transaction.txn_date.asc()).all()

    # CSV response
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Amount", "Type", "Remarks", "Bank"])
    for t in transactions:
        writer.writerow([
            t.txn_date.strftime("%Y-%m-%d"),
            t.amount,
            t.txn_type,
            t.remarks,
            t.bank
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=transactions.csv"
        }
    )




@stmt_bp.route('/import', methods=['POST'])
@jwt_required()
def import_statement():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл олдсонгүй'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл сонгоогүй байна'}), 400
    
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': 'Access token шаардлагатай'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join('/tmp', filename)
    file.save(filepath)

    try:
        # Excel унших
        df = pd.read_excel(filepath, engine='openpyxl', header=7)
        df.columns = df.columns.str.strip()
        print(f"📝 Columns: {df.columns.tolist()}")

        if not {'Гүйлгээний огноо', 'Дебит гүйлгээ', 'Кредит гүйлгээ', 'Гүйлгээний утга'}.issubset(df.columns):
            return jsonify({'error': 'Файлын толгой (header) тохирохгүй байна.'}), 400
        
        # Хэрэгтэй багануудыг сонго
        df = df[['Гүйлгээний огноо', 'Дебит гүйлгээ', 'Кредит гүйлгээ', 'Гүйлгээний утга']]

        # 🗑️ Хуучин гүйлгээг устгах
        db.session.query(Transaction).filter(Transaction.user_id == user_id).delete(synchronize_session=False)
        db.session.commit()

        inserted = 0
        for _, row in df.iterrows():
            if pd.isna(row['Гүйлгээний огноо']):
                continue
            
            txn_date = pd.to_datetime(row['Гүйлгээний огноо'], errors='coerce')
            if pd.isna(txn_date):
                continue
            txn_date = txn_date.date()

            debit_str = str(row['Дебит гүйлгээ']) if pd.notna(row['Дебит гүйлгээ']) else '0'
            credit_str = str(row['Кредит гүйлгээ']) if pd.notna(row['Кредит гүйлгээ']) else '0'

            try:
                debit = abs(float(debit_str.replace(',', '').replace('₮', '').replace('-', '').strip()))
            except:
                debit = 0.0
            try:
                credit = abs(float(credit_str.replace(',', '').replace('₮', '').replace('-', '').strip()))
            except:
                credit = 0.0

            # Excel дээр зарим debit багана сөрөг утга байж магадгүй тул abs() ашиглаж эерэг болгоно.
            if debit > 0:
                amount = -debit
                txn_type = 'out'
            elif credit > 0:
                amount = credit
                txn_type = 'in'
            else:
                continue  # 0 утгатай мөрийг алгасах

            remarks = str(row['Гүйлгээний утга']).strip() if pd.notna(row['Гүйлгээний утга']) else ''

            txn = Transaction(
                user_id=user_id,
                txn_date=txn_date,
                amount=amount,
                txn_type=txn_type,
                remarks=remarks,
                bank="KhanBank"
            )
            db.session.add(txn)
            inserted += 1


        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Алдаа: {str(e)}'}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.close()

    return jsonify({'message': f'✅ {inserted} гүйлгээг амжилттай импортлолоо.'}), 201



@stmt_bp.route('/total_income_expense', methods=['POST'])
@jwt_required()
def all_income_expense():
    user_id = get_jwt_identity()

    # Query all transactions for this user
    txns = Transaction.query.filter_by(user_id=user_id).all()

    if not txns:
        return jsonify({"error": "No transactions found."}), 404

    # Initialize totals
    total_income = 0.0
    total_expense = 0.0

    for txn in txns:
        if txn.txn_type == 'in':
            total_income += txn.amount
        elif txn.txn_type == 'out':
            total_expense += abs(txn.amount) 

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense
    }), 200


