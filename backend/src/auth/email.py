"""QQ 邮箱 SMTP 发送验证码"""
import smtplib
from email.mime.text import MIMEText
from backend.src.config.settings import settings


def send_verification_code(to_email: str, code: str) -> bool:
    """发送 6 位验证码到指定邮箱"""
    try:
        msg = MIMEText(
            f"【DevAssistant】您的验证码是：{code}，5 分钟内有效。",
            "plain", "utf-8",
        )
        msg["Subject"] = "DevAssistant 邮箱验证"
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email

        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False
