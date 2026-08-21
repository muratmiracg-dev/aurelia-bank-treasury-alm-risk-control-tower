from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    required = [
        "artifacts/results/executive_summary.json",
        "artifacts/results/eve.csv",
        "artifacts/results/nii.csv",
        "artifacts/results/liquidity.csv",
        "artifacts/results/data_quality_controls.csv",
        "artifacts/figures/executive-overview.png",
        "artifacts/aurelia_alm_demo.sqlite",
        "excel/Aurelia_Bank_ALCO_Risk_Workbench.xlsx",
        "presentation/Aurelia_Bank_ALM_Executive_Deck_EN.pptx",
        "report/Aurelia_Bank_ALM_Executive_Report.pdf",
        "powerbi/ALM_Measures.dax",
        "MANIFEST.sha256",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    summary = json.loads((root / required[0]).read_text(encoding="utf-8"))
    if summary["controls"]["data_quality_passed"] != summary["controls"]["data_quality_total"]:
        raise SystemExit("Not all data-quality controls passed")
    controls = pd.read_csv(root / "artifacts/results/data_quality_controls.csv")
    if set(controls["status"]) != {"PASS"}:
        raise SystemExit("Data-quality control file contains a failure")
    liquidity = pd.read_csv(root / "artifacts/results/liquidity.csv").set_index("scenario")
    if "rapid_digital_run" not in liquidity.index:
        raise SystemExit("Rapid digital-run liquidity scenario is missing")
    rapid = liquidity.loc["rapid_digital_run"]
    combined = liquidity.loc["combined"]
    if not rapid["lcr_proxy_pct"] < combined["lcr_proxy_pct"]:
        raise SystemExit("Rapid digital-run stress is not more severe than combined stress")
    if int(rapid["survival_horizon_days"]) != 7:
        raise SystemExit("Rapid digital-run survival horizon drifted from the governed snapshot")

    for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", maxsplit=1)
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Checksum mismatch: {relative}")
    print(f"Verified {len(required)} required artifacts and every manifest checksum.")


if __name__ == "__main__":
    main()
