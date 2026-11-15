import importlib.util
import json
import shutil
import sqlite3
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


@pytest.fixture(scope="module")
def pipeline_root(project_root: Path, tmp_path_factory) -> Path:
    """Regenerate the demo in a throwaway root so tests never rewrite committed outputs."""
    root = tmp_path_factory.mktemp("pipeline")
    shutil.copytree(project_root / "config", root / "config")
    run_pipeline(root)
    return root


def _load_compare_outputs(project_root: Path):
    spec = importlib.util.spec_from_file_location(
        "compare_outputs", project_root / "scripts" / "compare_outputs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pipeline_integration(pipeline_root: Path):
    summary = json.loads(
        (pipeline_root / "artifacts/results/executive_summary.json").read_text(encoding="utf-8")
    )
    assert summary["balance_sheet"]["assets_try_mn"] == 180_000
    assert summary["controls"]["data_quality_passed"] == 10
    assert summary["controls"]["risk_limit_breaches"] == 1
    assert (pipeline_root / "artifacts/aurelia_alm_demo.sqlite").exists()


def test_committed_outputs_match_regeneration(project_root: Path, pipeline_root: Path):
    compare_outputs = _load_compare_outputs(project_root)
    assert compare_outputs.compare(project_root, pipeline_root) == []


def test_compare_outputs_detects_stale_committed_outputs(
    project_root: Path, pipeline_root: Path, tmp_path: Path
):
    compare_outputs = _load_compare_outputs(project_root)
    stale = tmp_path / "stale"
    for relative in ("data/demo", "artifacts/results"):
        shutil.copytree(pipeline_root / relative, stale / relative)
    shutil.copy2(pipeline_root / compare_outputs.SQLITE_FILE, stale / compare_outputs.SQLITE_FILE)
    eve = pd.read_csv(stale / "artifacts/results/eve.csv")
    numeric = eve.select_dtypes("number").columns[0]
    eve.loc[0, numeric] = eve.loc[0, numeric] + 1.0
    eve.to_csv(stale / "artifacts/results/eve.csv", index=False, float_format="%.6f")
    summary_path = stale / "artifacts/results/executive_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["controls"]["risk_limit_breaches"] += 1
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with sqlite3.connect(stale / compare_outputs.SQLITE_FILE) as connection:
        connection.execute("DELETE FROM liquidity WHERE rowid = 1")

    errors = compare_outputs.compare(stale, pipeline_root)
    assert any(e.startswith(f"artifacts/results/eve.csv row 1 column {numeric}") for e in errors)
    assert any("executive_summary.json.controls.risk_limit_breaches" in e for e in errors)
    assert any(e.startswith(f"{compare_outputs.SQLITE_FILE}:liquidity") for e in errors)
    assert compare_outputs.main(["compare_outputs.py", str(stale), str(pipeline_root)]) == 1


def test_api_read_only_outputs(pipeline_root: Path, monkeypatch):
    monkeypatch.setenv("AURELIA_PROJECT_ROOT", str(pipeline_root))
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
