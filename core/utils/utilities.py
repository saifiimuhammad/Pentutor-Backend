import random
import smtplib
from email.mime.text import MIMEText
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    from email.mime.text import MIMEText
    import smtplib
    from django.conf import settings

    try:
        msg = MIMEText(f"Your OTP is: {otp}")
        msg['Subject'] = 'Verify your Email'
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = to_email

        print("📤 Sending email to:", to_email)
        print("📧 From:", settings.EMAIL_HOST_USER)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully!")

    except Exception as e:
        print("❌ Email sending failed:", e)
