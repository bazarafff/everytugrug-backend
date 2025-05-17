from flask_mail import Message
from app import mail
from flask import current_app

def send_alert_email(email, overspent_categories):
    with current_app.app_context():
        subject = "🚨 Overspending Alert - EveryTugrug"
        body = "You've overspent in the following categories:\n\n"

        for cat in overspent_categories:
            body += f"- {cat['category']}: Spent {cat['spent']} (Limit: {cat['limit']})\n"

        msg = Message(subject=subject, recipients=[email], body=body)
        mail.send(msg)
