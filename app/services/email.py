"""Synchronous SMTP email utilities (ported from Flask Celery blueprint)."""
import socket
import ssl
import base64
import time
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email_smtp(email: str, code: str, subject: str, body_template: str) -> None:
    """Low-level SMTP send via QQ mail (STARTTLS on port 587)."""
    sender_email = settings.QQ_SMTP_EMAIL
    authorization_code = settings.QQ_SMTP_AUTH_CODE

    if not sender_email or not authorization_code:
        raise RuntimeError("QQ_SMTP_EMAIL or QQ_SMTP_AUTH_CODE is not configured")

    text_content = body_template.format(code=code)

    msg = (
        f"From: {sender_email}\r\n"
        f"To: {email}\r\n"
        f"Subject: {subject}\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: multipart/mixed; boundary=boundary\r\n"
        "\r\n"
        "--boundary\r\n"
        "Content-Type: text/plain; charset=UTF-8\r\n"
        "\r\n"
        f"{text_content}\r\n"
        "--boundary\r\n"
    )
    endmsg = "\r\n.\r\n"
    mail_server = ("smtp.qq.com", 587)

    client_socket = None
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(mail_server)
        recv = client_socket.recv(1024).decode()
        if recv[:3] != "220":
            raise Exception("220 reply not received from server.")

        client_socket.send(b"HELO Alice\r\n")
        client_socket.recv(1024)

        client_socket.send(b"STARTTLS\r\n")
        client_socket.recv(1024)

        context = ssl.create_default_context()
        client_socket = context.wrap_socket(
            client_socket, server_hostname="smtp.qq.com"
        )

        client_socket.send(b"HELO Alice\r\n")
        client_socket.recv(1024)

        client_socket.send(b"AUTH LOGIN\r\n")
        client_socket.recv(1024)

        client_socket.send(base64.b64encode(sender_email.encode()) + b"\r\n")
        client_socket.recv(1024)

        client_socket.send(
            base64.b64encode(authorization_code.encode()) + b"\r\n"
        )
        client_socket.recv(1024)

        client_socket.send(f"MAIL FROM:<{sender_email}>\r\n".encode())
        client_socket.recv(1024)

        client_socket.send(f"RCPT TO:<{email}>\r\n".encode())
        client_socket.recv(1024)

        client_socket.send(b"DATA\r\n")
        client_socket.recv(1024)

        client_socket.send(msg.encode())
        client_socket.send(endmsg.encode())
        client_socket.recv(1024)

        client_socket.send(b"QUIT\r\n")
        time.sleep(1)
        client_socket.recv(1024)

    finally:
        if client_socket:
            client_socket.close()


def send_password_reset_email(email: str, code: str) -> None:
    """Send a password-reset verification code."""
    _send_email_smtp(
        email,
        code,
        subject="密码重置验证码",
        body_template="你好，这是您的密码重置验证码 {code}, 请在2分钟以内填写验证码",
    )


def send_login_verification_email(email: str, code: str) -> None:
    """Send an email-login verification code."""
    _send_email_smtp(
        email,
        code,
        subject="Email login verification code",
        body_template="Your login verification code is {code}. It expires in 5 minutes.",
    )


def send_landlord_upgrade_email(email: str, code: str) -> None:
    """Send a landlord-upgrade verification code."""
    _send_email_smtp(
        email,
        code,
        subject="申请房东身份",
        body_template="你好，这是您的验证码 {code}, 请在5分钟以内填写验证码",
    )
