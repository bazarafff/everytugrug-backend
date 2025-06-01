from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

categories = {
    "цалин": ["цалин", "salary", "цалин", "bonus", "step", "benefit", "ашиг"],
    "зээл": ["зээл", "loan", "installment", "ипотек", "ипотечный", "ипотек", "ипотекийн"],
    "хоол хүнс": ["хоол", "кафе", "рест", "food", "хүнс", "cafe", "restaurant", "coffee", "бар", "зоог", "pub", "snack"],
    "дэлгүүр": ["дэлгүүр", "nomin", "emart", "supermarket", "umd", "shop", "store", "mart", "ikhnomin", "oriflame", "avon"],
    "тээвэр": ["такси", "автобус", "ubcab", "taxi", "bus", "grab", "uber", "public transport"],
    "шатахуун": ["шатахуун", "бензин", "petrovis", "magnai", "refuel", "fuel", "petrol", "gasoline"],
    "эмчилгээ": ["эмнэлэг", "эм", "аптек", "shinjilgee", "vitamin", "clinic", "hospital", "pharmacy", "vitamins"],
    "төлбөр": ["төлбөр", "хураамж", "торгууль", "pay", "charge", "fine", "fee", "dues"],
    "тоглоом": ["тоглоом", "game", "play", "pc", "steam", "mobile game", "ps", "xbox", "console"],
    "энтэртаймант": ["shou", "concert", "event", "pivo", "arhi", "party", "karaoke", "gala", "show"],
    "хувцас": ["хувцас", "clothes", "fashion", "apparel", "zara", "h&m", "uniqlo", "levis"],
    "бусад": []
}

@jwt_required()
def expense_pie():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        if not transactions:
            return jsonify({"error": "Гүйлгээ олдсонгүй."}), 404

        df = pd.DataFrame([{
            "txnDate": txn.txn_date,
            "amount": txn.amount,
            "remarks": txn.remarks
        } for txn in transactions])

        df["debit"] = df["amount"].apply(lambda x: abs(x) if x < 0 else 0)
        df["description"] = df["remarks"].str.lower()

        def categorize(text):
            for cat, keys in categories.items():
                if any(k in text for k in keys):
                    return cat
            return "бусад"
        df["category"] = df["description"].apply(categorize)

        df_pie = df.groupby("category")["debit"].sum().reset_index()
        data = [
            {"category": row["category"], "debit": float(row["debit"])}
            for _, row in df_pie.iterrows()
        ]
        return jsonify({"categories": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jwt_required()
def forecast_plot():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        if not transactions:
            return jsonify({"error": "Гүйлгээ олдсонгүй."}), 404

        df = pd.DataFrame([{
            "txnDate": txn.txn_date,
            "amount": txn.amount
        } for txn in transactions])

        df["txnDate"] = pd.to_datetime(df["txnDate"])
        df["credit"] = df["amount"].apply(lambda x: x if x > 0 else 0)
        df["debit"] = df["amount"].apply(lambda x: abs(x) if x < 0 else 0)
        df["endBalance"] = df["amount"].cumsum()

        df_daily = df.groupby(df["txnDate"].dt.date)[["credit", "debit", "endBalance"]].sum().reset_index()
        df_daily["txnDate"] = pd.to_datetime(df_daily["txnDate"])
        df_daily["daysSinceStart"] = (df_daily["txnDate"] - df_daily["txnDate"].min()).dt.days

        X = df_daily[["daysSinceStart"]]
        y = df_daily["endBalance"]
        model = LinearRegression().fit(X, y)

        future_days = np.arange(X["daysSinceStart"].max() + 1, X["daysSinceStart"].max() + 8)
        future_dates = pd.date_range(df_daily["txnDate"].max() + pd.Timedelta(days=1), periods=7)
        predicted = model.predict(future_days.reshape(-1, 1))

        data = {
            "actual": [
                {"txnDate": str(row["txnDate"].date()), "endBalance": float(row["endBalance"])}
                for _, row in df_daily.iterrows()
            ],
            "forecast": [
                {"txnDate": str(date), "predictedEndBalance": float(pred)}
                for date, pred in zip(future_dates, predicted)
            ]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jwt_required()
def analyze_financial_data():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        if not transactions:
            return jsonify({"error": "Гүйлгээ олдсонгүй."}), 404

        df = pd.DataFrame([{
            "txnDate": txn.txn_date,
            "amount": txn.amount,
            "remarks": txn.remarks
        } for txn in transactions])

        df["txnDate"] = pd.to_datetime(df["txnDate"])
        df["credit"] = df["amount"].apply(lambda x: x if x > 0 else 0)
        df["debit"] = df["amount"].apply(lambda x: abs(x) if x < 0 else 0)
        df["netAmount"] = df["credit"] - df["debit"]
        df["activity"] = df["credit"].abs() + df["debit"].abs()
        df["weekday"] = df["txnDate"].dt.weekday
        df["hour"] = 12

        features = df[["credit", "debit", "netAmount", "activity", "weekday", "hour"]].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df["behaviorCluster"] = kmeans.fit_predict(X_scaled)

        cluster_stats = df.groupby("behaviorCluster")[["credit", "debit", "netAmount", "activity"]].mean()
        user_cluster = df["behaviorCluster"].mode()[0]
        cluster_data = cluster_stats.loc[user_cluster]
        is_spender = (
            (cluster_data["credit"] < cluster_stats["credit"].mean()) and 
            (cluster_data["debit"] > cluster_stats["debit"].mean()) and 
            (cluster_data["netAmount"] < 0)
        )
        label = "Үрэлгэн" if is_spender else "Тогтвортой"

        forecast = forecast_plot().get_json()["forecast"]

        return jsonify({
            "forecast": forecast,
            "behaviorSummary": cluster_stats.reset_index().to_dict(orient="records"),
            "predictedBehavior": label
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@jwt_required()
def daily_income_expense_chart():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        if not transactions:
            return jsonify({"error": "Гүйлгээ олдсонгүй."}), 404

        df = pd.DataFrame([{
            "txnDate": txn.txn_date,
            "amount": txn.amount
        } for txn in transactions])

        df["txnDate"] = pd.to_datetime(df["txnDate"])
        df["credit"] = df["amount"].apply(lambda x: x if x > 0 else 0)
        df["debit"] = df["amount"].apply(lambda x: abs(x) if x < 0 else 0)

        df_daily = df.groupby(df["txnDate"].dt.date)[["credit", "debit"]].sum().reset_index()
        df_daily["txnDate"] = df_daily["txnDate"].astype(str)

        data = [
            {"txnDate": row["txnDate"], "credit": float(row["credit"]), "debit": float(row["debit"])}
            for _, row in df_daily.iterrows()
        ]
        return jsonify({"dailySummary": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
