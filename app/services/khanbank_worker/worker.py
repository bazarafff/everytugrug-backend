from playwright.sync_api import sync_playwright
import pandas as pd
from app import db
from app.models.transaction import Transaction
import os

class KhanbankWorker:
    def __init__(self, task_queue, results):
        self.task_queue = task_queue
        self.results = results
        self.sessions = {}

    def run(self):
        while True:
            task = self.task_queue.get()
            try:
                if task.step == "start":
                    self.handle_start(task)
                elif task.step == "verify":
                    self.handle_verify(task)
            except Exception as e:
                self.results[task.session_id] = {"status": "error", "error": str(e)}

    def handle_start(self, task):
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto("https://e.khanbank.com/auth/login")
        page.fill('input#username', task.username)
        page.fill('input#password', task.password)
        page.click('button.login-button')

        page.wait_for_selector('input.ant-radio-input[value="SOTP"]', timeout=20000)
        page.check('input.ant-radio-input[value="SOTP"]')
        page.click('button:has-text("Үргэлжлүүлэх")')
        page.wait_for_selector('input#otp', timeout=60000)

        self.sessions[task.session_id] = {
            "playwright": p,
            "browser": browser,
            "context": context,
            "page": page,
        }
        if "user_id" not in self.results[task.session_id]:
            self.results[task.session_id]["user_id"] = task.user_id

        self.results[task.session_id]["status"] = "otp_sent"

    def handle_verify(self, task):
        session = self.sessions.get(task.session_id)
        if not session:
            self.results[task.session_id] = {"status": "error", "error": "Session not found"}
            return

        page = session["page"]
        page.wait_for_selector('input#otp', timeout=60000)
        page.fill('input#otp', task.otp_code)
        page.click('button[type="submit"]:has-text("Үргэлжлүүлэх")')

        try:
            page.wait_for_selector('span.ant-modal-close-x', timeout=5000)
            page.click('span.ant-modal-close-x')
        except:
            pass

        page.click('a.menu-item[href="/account"]')
        page.click('a.ctrl-btn:has-text("Хуулга")')
        page.click('button.btn-filter')
        page.click('div.search-item >> text=Сүүлийн 3 сар')
        page.click('button:has-text("Хайх")')

        with page.expect_download() as download_info:
            page.click('i.icon-xls')
        download = download_info.value
        xls_path = f"/tmp/{task.session_id}.xls"
        download.save_as(xls_path)

        try:
            df = pd.read_excel(xls_path, engine="xlrd")
            user_id = self.results[task.session_id]["user_id"]

            for _, row in df.iterrows():
                txn_date = pd.to_datetime(row['Гүйлгээний огноо'], errors='coerce').date()
                debit = float(str(row['Дебит гүйлгээ']).replace(',', '').replace('₮', '').strip()) if pd.notna(row['Дебит гүйлгээ']) else 0.0
                credit = float(str(row['Кредит гүйлгээ']).replace(',', '').replace('₮', '').strip()) if pd.notna(row['Кредит гүйлгээ']) else 0.0
                amount = credit - debit
                if amount == 0:
                    continue  # 0 amount бол хадгалахгүй
                txn_type = 'in' if amount > 0 else 'out'
                remarks = str(row['Гүйлгээний утга']) if pd.notna(row['Гүйлгээний утга']) else ''

                txn = Transaction(
                    user_id=user_id,
                    txn_date=txn_date,
                    amount=amount,
                    txn_type=txn_type,
                    remarks=remarks,
                    bank="KhanBank"
                )
                db.session.add(txn)
            db.session.commit()

            self.results[task.session_id] = {"status": "done"}

        except Exception as e:
            db.session.rollback()
            self.results[task.session_id] = {"status": "error", "error": f"DB insertion error: {str(e)}"}
        finally:
            # Excel файл ашигласны дараа устгах
            if os.path.exists(xls_path):
                os.remove(xls_path)
            db.session.close()
            session["browser"].close()
            session["playwright"].stop()
            del self.sessions[task.session_id]
