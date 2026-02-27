from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from config import MondayConfig


logger = logging.getLogger(__name__)

MONDAY_API_URL = "https://api.monday.com/v2"


@dataclass
class ClientRecord:
    client_id: str
    email: str
    feedback_link: str
    first_name: Optional[str] = None
    company: Optional[str] = None
    raw_item_id: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None


def _build_headers(config: MondayConfig) -> Dict[str, str]:
    return {
        "Authorization": config.api_token,
        "Content-Type": "application/json",
    }


def _extract_column_value(column_values: List[Dict[str, Any]], column_id: str) -> Optional[str]:
    for col in column_values:
        if col.get("id") == column_id:
            # Most monday.com columns put actual value in "text"
            text = col.get("text")
            if text:
                return text.strip()
            # Fallback to "value" JSON if needed
            value = col.get("value")
            if isinstance(value, str):
                return value.strip()
            return str(value) if value is not None else None
    return None


def fetch_clients(config: MondayConfig, limit: int = 500) -> List[ClientRecord]:
    """
    Fetch client records from a monday.com board.

    This uses a simple query that retrieves up to `limit` items from the board.
    If you need more than that, we can extend this to use pagination.
    """
    query = """
    query ($board_id: [ID!], $limit: Int!) {
      boards (ids: $board_id) {
        items_page (limit: $limit) {
          items {
            id
            name
            column_values {
              id
              text
              value
            }
          }
        }
      }
    }
    """

    variables = {
        "board_id": int(config.board_id),
        "limit": limit,
    }

    response = requests.post(
        MONDAY_API_URL,
        json={"query": query, "variables": variables},
        headers=_build_headers(config),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    print("DEBUG monday response:", data)

    # Surface GraphQL errors clearly
    errors = data.get("errors")
    if errors:
        raise RuntimeError(f"monday.com API error: {errors}")

    boards = data.get("data", {}).get("boards") or []
    if not boards:
        raise RuntimeError("No boards returned from monday.com. Check MONDAY_BOARD_ID and token permissions.")

    items_page = boards[0].get("items_page") or {}
    items = items_page.get("items") or []

    clients: List[ClientRecord] = []
    for item in items:
        column_values = item.get("column_values") or []

        email = _extract_column_value(column_values, config.email_column_id)
        client_id = _extract_column_value(column_values, config.client_id_column_id)
        feedback_link = _extract_column_value(column_values, config.feedback_link_column_id)
        first_name = (
            _extract_column_value(column_values, config.first_name_column_id)
            if config.first_name_column_id
            else None
        )
        company = (
            _extract_column_value(column_values, config.company_column_id)
            if config.company_column_id
            else None
        )

        if not email or not feedback_link:
            logger.debug(
                "Skipping item %s because of missing email or feedback link",
                item.get("id"),
            )
            continue

        record = ClientRecord(
            client_id=client_id or item.get("id", ""),
            email=email,
            feedback_link=feedback_link,
            first_name=first_name or item.get("name"),
            company=company,
            raw_item_id=int(item.get("id")) if item.get("id") is not None else None,
            raw=item,
        )
        clients.append(record)

    logger.info("Fetched %d client records from monday.com", len(clients))
    return clients

