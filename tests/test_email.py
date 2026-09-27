"""send_email: skipped without credentials, sent over STARTTLS, and never raises on SMTP errors."""

import logging
import smtplib
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.utils.email import send_email


@pytest.fixture
def smtp_configured(monkeypatch):
    monkeypatch.setattr(settings, "MAIL_USERNAME", "bot@example.com")
    monkeypatch.setattr(settings, "MAIL_PASSWORD", "app-password")
    monkeypatch.setattr(settings, "MAIL_FROM", "")
    monkeypatch.setattr(settings, "MAIL_SERVER", "smtp.example.com")
    monkeypatch.setattr(settings, "MAIL_PORT", 587)


def test_skipped_when_smtp_not_configured(monkeypatch, caplog):
    monkeypatch.setattr(settings, "MAIL_USERNAME", "")
    with patch("smtplib.SMTP") as smtp, caplog.at_level(logging.INFO):
        send_email("user@example.com", "Hi", "Body")
    smtp.assert_not_called()
    assert "SMTP not configured" in caplog.text


def test_sends_over_starttls(smtp_configured):
    with patch("smtplib.SMTP") as smtp:
        send_email("user@example.com", "Budget alert", "You spent 85%")

    smtp.assert_called_once_with("smtp.example.com", 587)
    server = smtp.return_value.__enter__.return_value
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("bot@example.com", "app-password")
    from_addr, to_addrs, message = server.sendmail.call_args.args
    assert from_addr == "bot@example.com"  # falls back to MAIL_USERNAME when MAIL_FROM is empty
    assert to_addrs == ["user@example.com"]
    assert "Subject: Budget alert" in message


def test_smtp_error_is_logged_not_raised(smtp_configured, caplog):
    with patch("smtplib.SMTP") as smtp, caplog.at_level(logging.ERROR):
        smtp.return_value.__enter__.return_value.login.side_effect = (
            smtplib.SMTPAuthenticationError(535, b"bad credentials")
        )
        send_email("user@example.com", "Hi", "Body")  # must not raise

    assert "Failed to send email to user@example.com" in caplog.text
