"""Adapters for official public data and committed reproducible snapshots."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .exceptions import ConfigurationError, DataQualityError


def load_tcmb_snapshot(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"as_of_date", "metric", "currency", "value", "source_url", "classification"}
    _require_columns(frame, required, "TCMB snapshot")
    frame["as_of_date"] = pd.to_datetime(frame["as_of_date"])
    return frame


def load_bddk_snapshot(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"period", "metric", "value", "unit", "source_url"}
    _require_columns(frame, required, "BDDK snapshot")
    frame["period"] = pd.to_datetime(frame["period"])
    if frame["metric"].duplicated().any():
        raise DataQualityError("BDDK snapshot contains duplicate metrics")
    return frame


EVDS_DEFAULT_BASE_URL = "https://evds3.tcmb.gov.tr/igmevdsms-dis/"


def build_evds_request(
    series: list[str],
    start_date: str,
    end_date: str,
    *,
    api_key: str,
    base_url: str | None = None,
) -> Request:
    """Build an EVDS3 series request following the TCMB web-service contract.

    EVDS3 appends parameters to the service path without ``?`` and requires the API
    key in the ``key`` HTTP header. The key is never placed in the URL, so it does not
    leak into proxy logs, shell history or error messages.
    """
    endpoint = base_url or os.getenv("EVDS_BASE_URL") or EVDS_DEFAULT_BASE_URL
    params = {
        "series": "-".join(series),
        "startDate": start_date,
        "endDate": end_date,
        "type": "json",
    }
    url = f"{endpoint.rstrip('/')}/{urlencode(params, safe='.-')}"
    return Request(url, headers={"key": api_key, "User-Agent": "aurelia-alm/1.0"})


def fetch_evds_series(
    series: list[str],
    start_date: str,
    end_date: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout_seconds: int = 30,
) -> pd.DataFrame:
    """Fetch an EVDS JSON payload when the user supplies their own API key.

    The demo pipeline never calls this function, so CI and local reproduction do not
    depend on network access or credentials.
    """
    key = api_key or os.getenv("EVDS_API_KEY")
    if not key:
        raise ConfigurationError("EVDS_API_KEY is required for live EVDS retrieval")
    if not series:
        raise ConfigurationError("At least one EVDS series must be requested")
    request = build_evds_request(series, start_date, end_date, api_key=key, base_url=base_url)
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - governed URL
        body = response.read().decode("utf-8")
    try:
        payload: Any = json.loads(body)
    except json.JSONDecodeError as exc:
        # The retired EVDS2 service path answers with the EVDS web application's HTML.
        raise DataQualityError(
            "EVDS response was not JSON; check EVDS_BASE_URL points to the EVDS3 "
            f"service ({EVDS_DEFAULT_BASE_URL})"
        ) from exc
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        raise DataQualityError("EVDS response did not contain an items list")
    return pd.DataFrame(items)


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise DataQualityError(f"{label} is missing columns: {sorted(missing)}")
