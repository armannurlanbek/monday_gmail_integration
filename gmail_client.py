from __future__ import annotations

import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GmailConfig


logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token file so re-consent happens.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _load_credentials(config: GmailConfig) -> Credentials:
    creds: Optional[Credentials] = None
    try:
        creds = Credentials.from_authorized_user_file(config.token_file, SCOPES)
    except Exception:
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(config.token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def _build_service(config: GmailConfig):
    creds = _load_credentials(config)
    service = build("gmail", "v1", credentials=creds)
    return service


def send_html_email(
    gmail_config: GmailConfig,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    cc_email: Optional[str] = None,
) -> None:
    """
    Send an HTML email (with plain-text fallback) via the Gmail API.
    """
    service = _build_service(gmail_config)

    message = MIMEMultipart("alternative")
    message["To"] = to_email
    message["From"] = gmail_config.sender_email
    message["Subject"] = subject
    if cc_email:
        message["Cc"] = cc_email

    part_text = MIMEText(text_body, "plain", "utf-8")
    part_html = MIMEText(html_body, "html", "utf-8")
    message.attach(part_text)
    message.attach(part_html)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    body = {"raw": raw}

    try:
        service.users().messages().send(userId="me", body=body).execute()
        logger.info("Sent email to %s (cc=%s)", to_email, cc_email or "")
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email to %s: %s", to_email, exc)
        raise

