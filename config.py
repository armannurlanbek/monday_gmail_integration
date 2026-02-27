import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass
class MondayConfig:
    api_token: str
    board_id: str
    email_column_id: str
    client_id_column_id: str
    feedback_link_column_id: str
    first_name_column_id: Optional[str] = None
    company_column_id: Optional[str] = None


@dataclass
class GmailConfig:
    sender_email: str
    credentials_file: str
    token_file: str = "token.json"


@dataclass
class AppConfig:
    monday: MondayConfig
    gmail: GmailConfig
    email_subject_template: str = "We'd love your feedback"
    dry_run: bool = False
    test_recipient: Optional[str] = None


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""


def load_config() -> AppConfig:
    monday = MondayConfig(
        api_token=_get_env("MONDAY_API_TOKEN", required=True),
        board_id=_get_env("MONDAY_BOARD_ID", required=True),
        email_column_id=_get_env("MONDAY_EMAIL_COLUMN_ID", required=True),
        client_id_column_id=_get_env("MONDAY_CLIENT_ID_COLUMN_ID", required=True),
        feedback_link_column_id=_get_env("MONDAY_FEEDBACK_LINK_COLUMN_ID", required=True),
        first_name_column_id=_get_env("MONDAY_FIRST_NAME_COLUMN_ID") or None,
        company_column_id=_get_env("MONDAY_COMPANY_COLUMN_ID") or None,
    )

    gmail = GmailConfig(
        sender_email=_get_env("GMAIL_SENDER_EMAIL", required=True),
        credentials_file=_get_env("GMAIL_CREDENTIALS_FILE", default="credentials.json", required=True),
        token_file=_get_env("GMAIL_TOKEN_FILE", default="token.json"),
    )

    app = AppConfig(
        monday=monday,
        gmail=gmail,
        email_subject_template=_get_env("EMAIL_SUBJECT_TEMPLATE", default="We'd love your feedback"),
        dry_run=_get_env("DRY_RUN", default="false").lower() == "true",
        test_recipient=_get_env("TEST_RECIPIENT") or None,
    )

    return app

