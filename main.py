from __future__ import annotations

import argparse
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from config import AppConfig, load_config
from email_template import build_email_html, build_subject
from gmail_client import send_html_email
from monday_client import ClientRecord, fetch_clients


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


MAX_ITEMS_FOR_NOW = 500
GLOBAL_CC_EMAIL = "karashn@orlanda.info"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send personalized HTML feedback emails based on a monday.com board."
    )
    parser.add_argument(
        "--client-id",
        help="Only send to a single client ID (as stored in the board).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do everything except actually send the emails.",
    )
    parser.add_argument(
        "--test-recipient",
        help="If set, send all emails to this address instead of the client's email.",
    )
    return parser.parse_args()


def filter_clients(clients: List[ClientRecord], client_id: Optional[str]) -> List[ClientRecord]:
    if not client_id:
        return clients
    return [c for c in clients if c.client_id == client_id]


def _split_emails(raw: str) -> List[str]:
    """
    Split a monday.com email column that may contain multiple emails.

    Supports comma/semicolon separation and trims whitespace.
    """
    if not raw:
        return []
    parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    return [p for p in parts if p]


def _log_send(
    log_path: Path,
    client: ClientRecord,
    recipient: str,
    board_id: str,
) -> None:
    """
    Append a log row for a successfully sent email.
    """
    is_new = not log_path.exists()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(
                [
                    "timestamp_utc",
                    "board_id",
                    "client_id",
                    "original_emails_cell",
                    "recipient_email",
                    "company",
                ]
            )
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                board_id,
                client.client_id,
                client.email,
                recipient,
                client.company or "",
            ]
        )


def main() -> None:
    args = parse_args()
    config: AppConfig = load_config()

    # Command-line flags override config defaults
    dry_run = args.dry_run or config.dry_run
    test_recipient = args.test_recipient or config.test_recipient

    logger.info(
        "Fetching up to %d clients from monday.com board %s",
        MAX_ITEMS_FOR_NOW,
        config.monday.board_id,
    )
    clients = fetch_clients(config.monday, limit=MAX_ITEMS_FOR_NOW)
    clients = filter_clients(clients, args.client_id)

    if not clients:
        logger.info("No clients found matching the specified filters.")
        return

    logger.info("Preparing to process %d client(s). Dry-run=%s", len(clients), dry_run)

    sent_count = 0
    failed_count = 0
    log_path = Path("sent_log.csv")

    for client in clients:
        subject = build_subject(client, config.email_subject_template)
        html_body, text_body = build_email_html(client)
        if test_recipient:
            recipients = [test_recipient]
        else:
            recipients = _split_emails(client.email)

        logger.info(
            "Processing client_id=%s emails=%s (actual recipients=%s)",
            client.client_id,
            client.email,
            recipients,
        )

        if dry_run:
            logger.info("Dry-run mode: not sending emails. Subject=%r", subject)
            continue

        for recipient in recipients:
            try:
                send_html_email(
                    gmail_config=config.gmail,
                    to_email=recipient,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    cc_email=GLOBAL_CC_EMAIL,
                )
                sent_count += 1
                _log_send(
                    log_path=log_path,
                    client=client,
                    recipient=recipient,
                    board_id=config.monday.board_id,
                )
            except Exception:  # noqa: BLE001
                failed_count += 1

    logger.info(
        "Done. Sent=%d, Failed=%d, Skipped(dry-run)=%s",
        sent_count,
        failed_count,
        dry_run,
    )


if __name__ == "__main__":
    main()

