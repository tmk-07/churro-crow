"""Google Sheets persistence for public practice leaderboards.

Credentials are loaded at runtime from environment variables or Streamlit
secrets. No credential material belongs in this repository.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Mapping

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build


MODE_TO_SHEET = {
    "Restriction Practice": "Restriction",
    "Padding Practice": "SetOperations",
    "Padding (w/ SymDiff)": "SymDiff",
}
SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)


class LeaderboardConfigurationError(RuntimeError):
    """Raised when leaderboard credentials have not been configured."""


def _as_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items()}


def _load_config() -> tuple[str, dict[str, Any]]:
    """Load Google configuration without exposing secret values in errors."""
    sheet_id = os.getenv("LEADERBOARD_SHEET_ID", "").strip()
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

    if sheet_id and service_account_json:
        try:
            account_info = json.loads(service_account_json)
        except json.JSONDecodeError as exc:
            raise LeaderboardConfigurationError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON."
            ) from exc
        return sheet_id, account_info

    try:
        leaderboard = st.secrets["leaderboard"]
        sheet_id = str(leaderboard["sheet_id"]).strip()
        account_info = _as_dict(leaderboard["service_account"])
    except (KeyError, TypeError, FileNotFoundError) as exc:
        raise LeaderboardConfigurationError(
            "Leaderboard access is not configured. Add Streamlit secrets or "
            "the LEADERBOARD_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON "
            "environment variables."
        ) from exc

    if not sheet_id or not account_info:
        raise LeaderboardConfigurationError(
            "Leaderboard configuration is incomplete."
        )
    return sheet_id, account_info


@st.cache_resource
def _get_sheets_service():
    sheet_id, account_info = _load_config()
    credentials = service_account.Credentials.from_service_account_info(
        account_info,
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    return sheet_id, service


def append_score(username: str, points: int, mode: str) -> None:
    sheet_id, service = _get_sheets_service()
    sheet_name = MODE_TO_SHEET.get(mode, "SetOperations")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    player = username.strip()[:40] or "Player"
    body = {"values": [[player, int(points), date_str]]}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A:C",
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()


def read_scores(mode: str) -> list[list[str]]:
    sheet_id, service = _get_sheets_service()
    sheet_name = MODE_TO_SHEET.get(mode, "SetOperations")
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A:C",
    ).execute()
    values = result.get("values", [])
    return values[1:] if len(values) > 1 else []
