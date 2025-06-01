from playwright.sync_api import sync_playwright
import pandas as pd
from app import db
from app.models.transaction import Transaction
import os

class GolomtBankWorker:
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

        page.goto("https://egolomt.mn/")
        page.fill('input[name="username"]', task.username)
        page.fill('input[name="password"]', task.password)
        page.click('button:has-text("Нэвтрэх")')
        page.locator('button.MuiButtonBase-root.MuiButton-contained').click()

        # OTP код хүлээх
        page.wait_for_selector('input[aria-label="Нэгдүгээр оролт"]', timeout=20000)
        
        self.sessions[task.session_id] = {
            "playwright": p,
            "browser": browser,
            "context": context,
            "page": page
        }
        self.results[task.session_id]["status"] = "otp_sent"
        self.results[task.session_id]["user_id"] = task.user_id

    def handle_verify(self, task):
        session = self.sessions.get(task.session_id)
        if not session:
            self.results[task.session_id] = {"status": "error", "error": "Session not found"}
            return

        page = session["page"]
        # OTP бөглөх
        otp_digits = list(task.otp_code)

        # Оролтын элементүүдийг хайж авах
        input_selectors = page.locator('input.pincode-input-text')

        for i, digit in enumerate(otp_digits):
            input_selectors.nth(i).fill(digit)  # Зөв selector ашиглах

        # "НЭВТРЭХ" товч дарах
        page.locator('button.MuiButtonBase-root.MuiButton-root.MuiButton-contained').click()

        try:
            # Данс хуулга татах процесс
            page.click('button:has-text("Харилцах данс")')
            page.click('button:has-text("Дансны хуулга")')
            page.click('div.MuiAutocomplete-root button.MuiButtonBase-root')
            page.click('li[role="option"]:has-text("3")')  # Сүүлийн 3 сар сонгох
            page.click('button:has-text("Хайх")')
            page.click('text=Excel хуулга')
            page.click('button:has-text("Татах")')

            with page.expect_download() as download_info:
                page.click('button:has-text("Бэлэн болсон хуулга татах")')
            download = download_info.value
            xls_path = f"/tmp/{task.session_id}.xlsx"
            download.save_as(xls_path)

            df = pd.read_excel(xls_path, engine='openpyxl')
            user_id = self.results[task.session_id]["user_id"]

            for _, row in df.iterrows():
                txn_date = pd.to_datetime(row['Гүйлгээний огноо'], errors='coerce').date()
                debit_str = str(row['Дебит гүйлгээ']) if pd.notna(row['Дебит гүйлгээ']) else '0'
                credit_str = str(row['Кредит гүйлгээ']) if pd.notna(row['Кредит гүйлгээ']) else '0'
                debit = float(debit_str.replace(',', '').replace('₮', '').strip()) if debit_str.strip() else 0.0
                credit = float(credit_str.replace(',', '').replace('₮', '').strip()) if credit_str.strip() else 0.0
                if credit > 0:
                    amount = credit
                    txn_type = 'in'
                elif debit > 0:
                    amount = -debit
                    txn_type = 'out'
                else:
                    continue
                remarks = str(row['Гүйлгээний утга']) if pd.notna(row['Гүйлгээний утга']) else ''
                txn = Transaction(user_id=user_id, txn_date=txn_date, amount=amount, txn_type=txn_type, remarks=remarks, bank="GolomtBank")
                db.session.add(txn)
            db.session.commit()

            self.results[task.session_id] = {"status": "done"}

        except Exception as e:
            db.session.rollback()
            self.results[task.session_id] = {"status": "error", "error": f"DB insertion error: {str(e)}"}
        finally:
            if os.path.exists(xls_path):
                os.remove(xls_path)
            db.session.close()
            session["browser"].close()
            session["playwright"].stop()
            del self.sessions[task.session_id]

