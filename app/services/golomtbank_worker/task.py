class Task:
    def __init__(self, session_id, username=None, password=None, otp_code=None, step=None):
        self.session_id = session_id
        self.username = username
        self.password = password
        self.otp_code = otp_code
        self.step = step
