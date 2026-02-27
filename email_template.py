from __future__ import annotations

from pathlib import Path
from typing import Tuple

from monday_client import ClientRecord


def build_subject(client: ClientRecord, subject_template: str) -> str:
    subject = subject_template
    replacements = {
        "{client_id}": client.client_id,
        "{first_name}": client.first_name or "",
        "{company}": client.company or "",
        "{email}": client.email,
    }
    for placeholder, value in replacements.items():
        subject = subject.replace(placeholder, value)
    return subject


def build_email_html(client: ClientRecord) -> Tuple[str, str]:
    """
    Build the HTML email from the external template file (email-he.html),
    inserting the client's ID into the monday.com form link (project_id=...),
    plus a simple plain-text fallback.
    """
    template_path = Path(__file__).with_name("email-he.html")
    html = template_path.read_text(encoding="utf-8")

    base_url = "https://forms.monday.com/forms/2609afb976ec2cabb2c0cd9113f8d683?r=euc1&project_id="
    custom_url = f"{base_url}{client.client_id}"

    # Replace all occurrences (the <a> href and the VML Outlook fallback)
    html = html.replace(base_url, custom_url)

    text = (
        "שלום,\n\n"
        "נשמח אם תוכל/י למלא את טופס המשוב בקישור הבא:\n"
        f"{custom_url}\n\n"
        f"Client ID: {client.client_id}\n"
    )

    return html, text


