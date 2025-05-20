import threading
import uuid
from flask_jwt_extended import get_jwt_identity
from playwright.sync_api import sync_playwright
import pandas as pd
from app.services import model
from app.models.statement_result import StatementResult
from app import db

# Store username/password per session ID only
pending_sessions = {}

def start_login_session(username, password, user_id):
    session_id = str(uuid.uuid4())
    pending_sessions[session_id] = {
        "username": username,
        "password": password,
        "user_id": user_id
    }
    return session_id



def submit_otp(session_id, otp_code):
    session = pending_sessions.get(session_id)
    if not session:
        raise Exception("Session expired or not found")

    username = session["username"]
    password = session["password"]
    user_id = session["user_id"]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            page.goto("https://e.khanbank.com/auth/login")
            page.fill('input#username', username)
            page.fill('input#password', password)
            page.click('button.login-button')

            page.wait_for_selector('input.ant-radio-input[value="SOTP"]', timeout=10000)
            page.check('input.ant-radio-input[value="SOTP"]')
            page.click('button:has-text("Үргэлжлүүлэх")')

            page.wait_for_selector('input#otp', timeout=10000)
            page.fill('input#otp', otp_code)
            page.click('button[type="submit"]:has-text("Үргэлжлүүлэх")')

            page.wait_for_selector('a.ctrl-btn:has-text("Хуулга")', timeout=15000)
            page.click('a.ctrl-btn:has-text("Хуулга")')

            page.wait_for_selector('i.icon-xls', timeout=10000)
            with page.expect_download() as download_info:
                page.click('i.icon-xls')
            download = download_info.value
            download.save_as("khanbank_statement.xls")

            df = pd.read_excel("khanbank_statement.xls", engine="xlrd")
            df.to_excel("khanbank_statement_converted.xlsx", index=False)

            result = model.analyze_financial_data(as_json=True)
            record = StatementResult(user_id=user_id, analyzed_json=result)
            db.session.add(record)
            db.session.commit()

            return result

    finally:
        # Clear session after use
        pending_sessions.pop(session_id, None)