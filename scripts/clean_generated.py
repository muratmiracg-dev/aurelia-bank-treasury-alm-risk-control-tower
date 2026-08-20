from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    targets = [
        root / "data" / "demo",
        root / "artifacts" / "results",
        root / "artifacts" / "figures",
    ]
    for target in targets:
        if target.exists():
            for path in target.glob("*"):
                if path.is_file():
                    path.unlink()
    for path in [root / "artifacts" / "aurelia_alm_demo.sqlite", root / "MANIFEST.sha256"]:
        if path.exists():
            path.unlink()
