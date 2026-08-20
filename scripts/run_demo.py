from pathlib import Path

from aurelia_alm.pipeline import run_pipeline

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    summary = run_pipeline(project_root)
    print(f"Pipeline complete: {summary['project']} as of {summary['as_of_date']}")
