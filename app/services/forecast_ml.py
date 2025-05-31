from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.transaction import Transaction
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta

def forecast_next_week_balance():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.txn_date).all()
    if not transactions:
        return jsonify({"error": "Гүйлгээ олдсонгүй"}), 404

    df = pd.DataFrame([{
        "txn_date": txn.txn_date,
        "amount": txn.amount
    } for txn in transactions])

    df["txn_date"] = pd.to_datetime(df["txn_date"])
    df = df.groupby(df["txn_date"].dt.date)["amount"].sum().reset_index()
    df = df.rename(columns={"txn_date": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").asfreq("D", fill_value=0)
    df["cumsum_balance"] = df["amount"].cumsum()

    model = ARIMA(df["cumsum_balance"], order=(5,1,0))
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=7)
    last_date = df.index.max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(7)]
    forecast_data = [{"date": str(future_dates[i]), "predicted_end_balance": float(forecast[i])} for i in range(7)]

    return jsonify({
        "forecast": forecast_data
    })
