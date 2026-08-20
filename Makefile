.PHONY: install demo test coverage quality verify api clean

install:
	python -m pip install -e ".[dev]"

demo:
	python scripts/run_demo.py

test:
	pytest

coverage:
	pytest --cov=aurelia_alm --cov-report=term-missing --cov-fail-under=90

quality:
	ruff format --check .
	ruff check .

verify: quality coverage demo
	python scripts/verify_artifacts.py

api:
	uvicorn aurelia_alm.api:app --host 0.0.0.0 --port 8000

clean:
	python scripts/clean_generated.py

