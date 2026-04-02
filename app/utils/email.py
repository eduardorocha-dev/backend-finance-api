"""Email sending utility using stdlib smtplib.

Sends emails via the SMTP server configured in settings.
If MAIL_USERNAME is not set the call is a no-op so the app works
in development without any email credentials configured.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email.

    Silently skips if MAIL_USERNAME is not configured so that
    development environments work without SMTP credentials.
    """
    if not settings.MAIL_USERNAME:
        logger.info("SMTP not configured — skipping email to %s: %s", to, subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_FROM or settings.MAIL_USERNAME
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(msg["From"], [to], msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s", to)
