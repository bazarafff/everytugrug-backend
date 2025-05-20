from playwright.sync_api import sync_playwright
import pandas as pd

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
        browser = p.chromium.launch(headless=False, args=["--window-position=-10000,-10000"])
  # MUST be False to see browser
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto("https://e.khanbank.com/auth/login")
        page.fill('input#username', task.username)
        page.fill('input#password', task.password)
        page.click('button.login-button')

        # Select OTP option and proceed
        page.wait_for_selector('input.ant-radio-input[value="SOTP"]', timeout=20000)
        page.check('input.ant-radio-input[value="SOTP"]')
        page.click('button:has-text("Үргэлжлүүлэх")')

        # ✅ Wait for OTP input field to appear — triggers SMS
        page.wait_for_selector('input#otp', timeout=60000)

        # Save session for /crawl/verify step
        self.sessions[task.session_id] = {
            "playwright": p,
            "browser": browser,
            "context": context,
            "page": page,
        }

        self.results[task.session_id] = {"status": "otp_sent"}

    def handle_verify(self, task):
        session = self.sessions.get(task.session_id)
        if not session:
            raise ValueError("Session not found")

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
        xls_path = f"{task.session_id}.xls"
        download.save_as(xls_path)

        df = pd.read_excel(xls_path, engine="xlrd")
        xlsx_path = f"{task.session_id}.xlsx"
        df.to_excel(xlsx_path, index=False)

        # Clean up
        session["browser"].close()
        session["playwright"].stop()
        del self.sessions[task.session_id]

        self.results[task.session_id] = {"status": "done", "file": xlsx_path}
