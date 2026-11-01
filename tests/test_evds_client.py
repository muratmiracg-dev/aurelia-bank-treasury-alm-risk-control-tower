"""EVDS3 live connector contract, tested without network access."""

import io
import json

import pytest

from aurelia_alm import data_sources
from aurelia_alm.data_sources import (
    EVDS_DEFAULT_BASE_URL,
    build_evds_request,
    fetch_evds_series,
)
from aurelia_alm.exceptions import DataQualityError

SECRET = "test-secret-key"


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def captured(monkeypatch):
    calls = {}

    def respond_with(body: bytes):
        def fake_urlopen(request, timeout):
            calls["request"] = request
            calls["timeout"] = timeout
            return _Response(body)

        monkeypatch.setattr(data_sources, "urlopen", fake_urlopen)
        return calls

    monkeypatch.delenv("EVDS_BASE_URL", raising=False)
    return respond_with


def test_request_uses_evds3_path_style_url():
    request = build_evds_request(
        ["TP.DK.USD.A.YTL", "TP.DK.EUR.A.YTL"], "01-01-2026", "31-01-2026", api_key=SECRET
    )
    assert request.full_url == (
        "https://evds3.tcmb.gov.tr/igmevdsms-dis/"
        "series=TP.DK.USD.A.YTL-TP.DK.EUR.A.YTL&startDate=01-01-2026&endDate=31-01-2026&type=json"
    )
    assert "?" not in request.full_url


def test_api_key_is_sent_only_in_header():
    request = build_evds_request(["TP.POLICY"], "01-01-2026", "01-02-2026", api_key=SECRET)
    assert request.get_header("Key") == SECRET
    assert SECRET not in request.full_url


def test_base_url_override_from_argument_and_environment(monkeypatch):
    request = build_evds_request(
        ["S"], "01-01-2026", "01-02-2026", api_key=SECRET, base_url="https://mirror.test/api"
    )
    assert request.full_url.startswith("https://mirror.test/api/series=S&")
    monkeypatch.setenv("EVDS_BASE_URL", "https://env.test/evds/")
    request = build_evds_request(["S"], "01-01-2026", "01-02-2026", api_key=SECRET)
    assert request.full_url.startswith("https://env.test/evds/series=S&")
    monkeypatch.setenv("EVDS_BASE_URL", "")
    request = build_evds_request(["S"], "01-01-2026", "01-02-2026", api_key=SECRET)
    assert request.full_url.startswith(EVDS_DEFAULT_BASE_URL)


def test_fetch_parses_items(captured):
    payload = {"totalCount": 2, "items": [{"Tarih": "01-01-2026"}, {"Tarih": "02-01-2026"}]}
    calls = captured(json.dumps(payload).encode())
    frame = fetch_evds_series(["S"], "01-01-2026", "02-01-2026", api_key=SECRET, timeout_seconds=7)
    assert list(frame["Tarih"]) == ["01-01-2026", "02-01-2026"]
    assert calls["timeout"] == 7
    assert calls["request"].get_header("Key") == SECRET


def test_fetch_reads_key_from_environment(captured, monkeypatch):
    calls = captured(b'{"items": []}')
    monkeypatch.setenv("EVDS_API_KEY", "env-key")
    assert fetch_evds_series(["S"], "01-01-2026", "02-01-2026").empty
    assert calls["request"].get_header("Key") == "env-key"


def test_html_response_from_retired_endpoint_is_explained(captured):
    captured(b"<!doctype html><html><body>EVDS</body></html>")
    with pytest.raises(DataQualityError, match="not JSON.*EVDS3"):
        fetch_evds_series(["S"], "01-01-2026", "02-01-2026", api_key=SECRET)


@pytest.mark.parametrize("body", [b'{"totalCount": 0}', b'["not", "a", "dict"]'])
def test_payload_without_items_list_is_rejected(captured, body):
    captured(body)
    with pytest.raises(DataQualityError, match="items list"):
        fetch_evds_series(["S"], "01-01-2026", "02-01-2026", api_key=SECRET)
