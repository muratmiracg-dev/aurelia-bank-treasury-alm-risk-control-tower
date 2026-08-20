"""Read-only decision-support API over verified pipeline outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI(
    title="Aurelia Bank Treasury & ALM API",
    version="1.0.0",
    description="Read-only access to synthetic ALM decision-support outputs.",
)


def _root() -> Path:
    return Path(os.getenv("AURELIA_PROJECT_ROOT", ".")).resolve()


def _authorize(x_api_key: str | None = Header(default=None)) -> None:
    configured = os.getenv("AURELIA_API_KEY", "")
    if configured and x_api_key != configured:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _read_csv(name: str) -> list[dict[str, object]]:
    path = _root() / "artifacts" / "results" / f"{name}.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Pipeline outputs are not available")
    return pd.read_csv(path).to_dict(orient="records")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    summary = _root() / "artifacts" / "results" / "executive_summary.json"
    if not summary.exists():
        raise HTTPException(status_code=503, detail="Run the pipeline first")
    return {"status": "ready"}


@app.get("/api/v1/summary", dependencies=[Depends(_authorize)])
def summary() -> dict[str, object]:
    path = _root() / "artifacts" / "results" / "executive_summary.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Pipeline outputs are not available")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/v1/irrbb/eve", dependencies=[Depends(_authorize)])
def irrbb_eve() -> list[dict[str, object]]:
    return _read_csv("eve")


@app.get("/api/v1/irrbb/nii", dependencies=[Depends(_authorize)])
def irrbb_nii() -> list[dict[str, object]]:
    return _read_csv("nii")


@app.get("/api/v1/liquidity", dependencies=[Depends(_authorize)])
def liquidity() -> list[dict[str, object]]:
    return _read_csv("liquidity")


@app.get("/api/v1/hedges", dependencies=[Depends(_authorize)])
def hedges() -> list[dict[str, object]]:
    return _read_csv("hedges")
