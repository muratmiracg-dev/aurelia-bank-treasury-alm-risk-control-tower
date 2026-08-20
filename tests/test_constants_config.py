from pathlib import Path

import pytest
import yaml

from aurelia_alm.config import load_project_config, load_yaml, validate_project_config
from aurelia_alm.constants import bucket_for_years, liquidity_bucket_for_days
from aurelia_alm.exceptions import ConfigurationError


def test_bucket_boundaries():
    assert bucket_for_years(0).label == "ON"
    assert bucket_for_years(0.20).label == "1M-3M"
    assert bucket_for_years(3.5).label == "3Y-4Y"
    assert bucket_for_years(30).label == ">20Y"


def test_negative_tenor_rejected():
    with pytest.raises(ValueError):
        bucket_for_years(-0.01)


def test_liquidity_buckets():
    assert liquidity_bucket_for_days(1) == "1D"
    assert liquidity_bucket_for_days(8) == "30D"
    assert liquidity_bucket_for_days(400) == ">1Y"
    with pytest.raises(ValueError):
        liquidity_bucket_for_days(-1)


def test_load_project_config(config):
    assert config["assumptions"]["reporting_currency"] == "TRY"
    assert config["shocks"]["currencies"]["TRY"]["parallel"] == 400


def test_missing_yaml_raises(tmp_path: Path):
    with pytest.raises(ConfigurationError):
        load_yaml(tmp_path / "missing.yml")


def test_non_mapping_yaml_raises(tmp_path: Path):
    path = tmp_path / "bad.yml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_yaml(path)


def test_curve_length_validation(config):
    broken = yaml.safe_load(yaml.safe_dump(config))
    broken["assumptions"]["curve_calibration"]["TRY"] = [1.0]
    with pytest.raises(ConfigurationError):
        validate_project_config(broken)


def test_missing_currency_validation(config):
    broken = yaml.safe_load(yaml.safe_dump(config))
    del broken["shocks"]["currencies"]["EUR"]
    with pytest.raises(ConfigurationError):
        validate_project_config(broken)


def test_non_positive_shock_validation(config):
    broken = yaml.safe_load(yaml.safe_dump(config))
    broken["shocks"]["currencies"]["USD"]["short"] = 0
    with pytest.raises(ConfigurationError):
        validate_project_config(broken)


def test_load_project_config_missing_root(tmp_path: Path):
    with pytest.raises(ConfigurationError):
        load_project_config(tmp_path)
