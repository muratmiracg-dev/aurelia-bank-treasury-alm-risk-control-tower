from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from aurelia_alm.api import app
from aurelia_alm.data_sources import fetch_evds_series, load_bddk_snapshot, load_tcmb_snapshot
from aurelia_alm.exceptions import ConfigurationError, DataQualityError
from aurelia_alm.pipeline import run_pipeline


def test_official_snapshots_load(project_root: Path):
    tcmb = load_tcmb_snapshot(project_root / "data/external/tcmb_market_snapshot.csv")
    bddk = load_bddk_snapshot(project_root / "data/external/bddk_sector_snapshot.csv")
    assert tcmb.loc[tcmb["metric"] == "policy_rate", "value"].iloc[0] == 37.0
    assert bddk.loc[bddk["metric"] == "total_assets", "value"].iloc[0] == 52_727_562


def test_snapshot_missing_columns(tmp_path: Path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"x": [1]}).to_csv(path, index=False)
    with pytest.raises(DataQualityError):
        load_tcmb_snapshot(path)
    with pytest.raises(DataQualityError):
        load_bddk_snapshot(path)


def test_bddk_duplicate_metric(tmp_path: Path):
    path = tmp_path / "duplicate.csv"
    pd.DataFrame(
        {
            "period": ["2026-06-30", "2026-06-30"],
            "metric": ["assets", "assets"],
            "value": [1, 1],
            "unit": ["TRY", "TRY"],
            "source_url": ["https://example.com", "https://example.com"],
        }
    ).to_csv(path, index=False)
    with pytest.raises(DataQualityError):
        load_bddk_snapshot(path)


def test_evds_requires_key(monkeypatch):
    monkeypatch.delenv("EVDS_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        fetch_evds_series(["TP.POLICY"], "01-01-2026", "01-02-2026")
    with pytest.raises(ConfigurationError):
        fetch_evds_series([], "01-01-2026", "01-02-2026", api_key="x")


def test_pipeline_integration(project_root: Path):
    summary = run_pipeline(project_root)
    assert summary["balance_sheet"]["assets_try_mn"] == 180_000
    assert summary["controls"]["data_quality_passed"] == 10
    assert summary["controls"]["risk_limit_breaches"] == 1
    assert (project_root / "artifacts/aurelia_alm_demo.sqlite").exists()


def test_api_read_only_outputs(project_root: Path, monkeypatch):
    run_pipeline(project_root)
    monkeypatch.setenv("AURELIA_PROJECT_ROOT", str(project_root))
    client = TestClient(app)
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    summary = client.get("/api/v1/summary")
    assert summary.status_code == 200
    assert summary.json()["project"].startswith("Aurelia Bank")
    assert len(client.get("/api/v1/irrbb/eve").json()) == 24
    assert len(client.get("/api/v1/irrbb/nii").json()) == 2
    liquidity = client.get("/api/v1/liquidity").json()
    assert len(liquidity) == 5
    rapid = next(row for row in liquidity if row["scenario"] == "rapid_digital_run")
    assert rapid["survival_horizon_days"] == 7
    assert len(client.get("/api/v1/hedges").json()) == 5


def test_api_key_and_missing_outputs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AURELIA_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("AURELIA_API_KEY", "secret")
    client = TestClient(app)
    assert client.get("/health/ready").status_code == 503
    assert client.get("/api/v1/summary").status_code == 401
    assert client.get("/api/v1/summary", headers={"X-API-Key": "secret"}).status_code == 503
