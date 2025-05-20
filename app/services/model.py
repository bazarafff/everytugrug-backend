import io
import pandas as pd
import matplotlib.pyplot as plt
from flask import request, jsonify, send_file
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import datetime as dt
import matplotlib

matplotlib.use("Agg")


def expense_pie():
    try:
        df_raw = pd.read_excel("khanbank_statement_converted.xlsx", header=None)

        matched = df_raw[df_raw.apply(lambda row: row.astype(str).str.contains("Гүйлгээний огноо").any(), axis=1)]
        if matched.empty:
            return jsonify({"error": "'Гүйлгээний огноо' багана олдсонгүй. Буруу файл байж магадгүй."}), 400

        start_index = matched.index[0]
        df = pd.read_excel("khanbank_statement_converted.xlsx", header=start_index)

        required_cols = {'Гүйлгээний огноо', 'Дебит гүйлгээ', 'Гүйлгээний утга'}
        if not required_cols.issubset(set(df.columns)):
            return jsonify({"error": "Шаардлагатай баганууд байхгүй байна."}), 400

        df = df[['Гүйлгээний огноо', 'Дебит гүйлгээ', 'Гүйлгээний утга']].copy()
        df.columns = ["txn_date", "debit", "description"]
        df["debit"] = pd.to_numeric(df["debit"].astype(str).str.replace(",", "").str.replace("₮", ""), errors="coerce").fillna(0)
        df["description"] = df["description"].astype(str).str.lower()

        categories = {
            "цалин": ["цалин", "salary"],
            "зээл": ["зээл", "loan"],
            "хоол хүнс": ["хоол", "кафе", "рест", "food", "хүнс"],
            "дэлгүүр": ["дэлгүүр", "nomin", "emart", "supermarket", "umd"],
            "тээвэр": ["такси", "автобус", "ubcab", "taxi"],
            "шатахуун": ["шатахуун", "бензин", "petrovis", "magnai"],
            "эмчилгээ": ["эмнэлэг", "эм", "аптек", "shinjilgee", "vitamin"],
            "төлбөр": ["төлбөр", "хураамж", "торгууль"],
            "тоглоом": ["тоглоом", "game", "play", "pc"],
            "угаалга шоу": ["shou", "concert", "event", "pivo", "arhi"],
            "бусад": []
        }

        def categorize(text):
            for cat, keys in categories.items():
                if any(k in text for k in keys):
                    return cat
            return "бусад"

        df["category"] = df["description"].apply(categorize)
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0).abs()

        df_pie = df.groupby("category")["debit"].sum()
        df_pie = df_pie[df_pie > 0].sort_values(ascending=False)

        if df_pie.empty:
            return jsonify({"error": "Ангилсан зарлагын дата хоосон байна."}), 400

        plt.figure(figsize=(10, 6))
        df_pie.plot(kind="bar", color="skyblue")
        plt.title("Зарлагын ангилалтай Bar Chart")
        plt.xlabel("Ангилал")
        plt.ylabel("Зарлагын дүн (₮)")
        plt.xticks(rotation=45)
        plt.grid(axis="y")
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close()

        return send_file(img, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def forecast_plot():
    try:
        df_raw = pd.read_excel("khanbank_statement_converted.xlsx", header=None)
        start_index = df_raw[df_raw.apply(lambda row: row.astype(str).str.contains("Гүйлгээний огноо").any(), axis=1)].index[0]
        df = pd.read_excel("khanbank_statement_converted.xlsx", header=start_index)

        df = df[['Гүйлгээний огноо', 'Эхний үлдэгдэл', 'Дебит гүйлгээ', 'Кредит гүйлгээ', 'Эцсийн үлдэгдэл']].copy()
        df.columns = ["txn_date", "begin_balance", "debit", "credit", "end_balance"]
        for col in ["begin_balance", "debit", "credit", "end_balance"]:
            df[col] = df[col].astype(str).str.replace(",", "").str.replace("₮", "").astype(float)
        df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce")

        df_daily = df.groupby(df["txn_date"].dt.date)[["credit", "debit", "end_balance"]].sum().reset_index()
        df_daily["txn_date"] = pd.to_datetime(df_daily["txn_date"])
        df_daily["days_since_start"] = (df_daily["txn_date"] - df_daily["txn_date"].min()).dt.days

        X = df_daily[["days_since_start"]]
        y = df_daily["end_balance"]

        model = LinearRegression()
        model.fit(X, y)

        future_days = np.arange(X["days_since_start"].max() + 1, X["days_since_start"].max() + 8)
        future_dates = pd.date_range(df_daily["txn_date"].max() + pd.Timedelta(days=1), periods=7)
        predicted = model.predict(future_days.reshape(-1, 1))

        plt.figure(figsize=(10, 6))
        plt.plot(df_daily["txn_date"], y, label="Бодит үлдэгдэл")
        plt.plot(future_dates, predicted, label="Таамаг үлдэгдэл", linestyle="--", marker='o')
        plt.xlabel("Огноо")
        plt.ylabel("Үлдэгдэл (₮)")
        plt.title("🔮 Ирээдүйн үлдэгдлийн таамаглал")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def analyze_financial_data():
    try:
        df_raw = pd.read_excel("khanbank_statement_converted.xlsx", header=None)
        start_index = df_raw[df_raw.apply(lambda row: row.astype(str).str.contains("Гүйлгээний огноо").any(), axis=1)].index[0]
        df = pd.read_excel("khanbank_statement_converted.xlsx", header=start_index)

        df = df[[
            'Гүйлгээний огноо', 'Эхний үлдэгдэл', 'Дебит гүйлгээ', 'Кредит гүйлгээ',
            'Эцсийн үлдэгдэл', 'Гүйлгээний утга', 'Харьцсан данс'
        ]].copy()
        df.columns = ["txn_date", "begin_balance", "debit", "credit", "end_balance", "description", "counterparty"]

        for col in ["begin_balance", "debit", "credit", "end_balance"]:
            df[col] = df[col].astype(str).str.replace(",", "").str.replace("₮", "").astype(float)

        df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce")

        df_daily = df.groupby(df["txn_date"].dt.date)[["credit", "debit", "end_balance"]].sum().reset_index()
        df_daily["txn_date"] = pd.to_datetime(df_daily["txn_date"])
        df_daily["days_since_start"] = (df_daily["txn_date"] - df_daily["txn_date"].min()).dt.days

        X = df_daily[["days_since_start"]]
        y = df_daily["end_balance"]

        model = LinearRegression()
        model.fit(X, y)

        future_days = np.arange(X["days_since_start"].max() + 1, X["days_since_start"].max() + 8)
        predicted = model.predict(future_days.reshape(-1, 1)).tolist()

        df["net_amount"] = df["credit"] - df["debit"]
        df["activity"] = df["credit"].abs() + df["debit"].abs()
        df["weekday"] = df["txn_date"].dt.weekday
        df["hour"] = df["txn_date"].dt.hour

        features = df[["credit", "debit", "net_amount", "activity", "weekday", "hour"]].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df["behavior_cluster"] = kmeans.fit_predict(X_scaled)

        cluster_stats = df.groupby("behavior_cluster")[["credit", "debit", "net_amount", "activity"]].mean()
        user_cluster = df["behavior_cluster"].mode()[0]
        cluster_data = cluster_stats.loc[user_cluster]

        is_spender = (
            (cluster_data["credit"] < cluster_stats["credit"].mean()) and
            (cluster_data["debit"] > cluster_stats["debit"].mean()) and
            (cluster_data["net_amount"] < 0)
        )

        label = "Үрэлгэн" if is_spender else "Тогтвортой"

        return jsonify({
            "үлдэгдлийн_таамаглал": predicted,
            "зан_төлөв": label
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
