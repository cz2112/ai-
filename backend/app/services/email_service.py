# backend/app/services/email_service.py
import os
from datetime import datetime, timedelta
from jose import jwt

async def send_verification_email(email: str, user_id: int, secret_key: str):
    """发送邮箱验证邮件"""
    mail_username = os.getenv("MAIL_USERNAME", "")
    if not mail_username:
        print(f"[跳过邮件] 未配置邮箱，验证链接: /api/auth/verify-email?token=...")
        return False
    
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    
    conf = ConnectionConfig(
        MAIL_USERNAME=mail_username,
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", mail_username),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.qq.com"),
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        MAIL_FROM_NAME="Smart Study Assistant",
    )
    
    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=24)},
        secret_key,
        algorithm="HS256"
    )
    link = f"http://localhost:8000/api/auth/verify-email?token={token}"
    
    html_content = f"""
    <html>
    <body>
        <h2>欢迎使用 Smart Study Assistant！</h2>
        <p>请点击下方链接验证您的邮箱（24小时内有效）：</p>
        <a href="{link}">{link}</a>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="验证您的邮箱 - Smart Study Assistant",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    return True


async def send_reset_password_email(email: str, user_id: int, secret_key: str):
    """发送密码重置邮件"""
    mail_username = os.getenv("MAIL_USERNAME", "")
    if not mail_username:
        print(f"[跳过邮件] 未配置邮箱，重置链接: /reset-password?token=...")
        return False
    
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    
    conf = ConnectionConfig(
        MAIL_USERNAME=mail_username,
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", mail_username),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.qq.com"),
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        MAIL_FROM_NAME="Smart Study Assistant",
    )
    
    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=1)},
        secret_key,
        algorithm="HS256"
    )
    link = f"http://localhost:5173/reset-password?token={token}"
    
    html_content = f"""
    <html>
    <body>
        <h2>重置您的密码</h2>
        <p>请点击下方链接重置密码（1小时内有效）：</p>
        <a href="{link}">{link}</a>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="重置密码 - Smart Study Assistant",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    return True