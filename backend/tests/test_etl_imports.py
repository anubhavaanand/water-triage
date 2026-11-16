"""Import-level guards for the ETL scripts.

These run every script's import path so a stale symbol fails here instead of
crashing the operator mid-run.
"""

import importlib

import pytest

SCRIPTS = [
    "etl.repair_readings",
    "etl.load_wqmis",
    "etl.load_data",
]


@pytest.mark.parametrize("module_name", SCRIPTS)
def test_etl_module_imports(module_name):
    importlib.import_module(module_name)


def test_repair_readings_uses_existing_symbols():
    from etl import load_wqmis, repair_readings

    assert repair_readings.RAW_JSONL is load_wqmis.RAW_JSONL
    assert callable(repair_readings.map_param)


def test_map_param_maps_known_labels():
    from etl.load_wqmis import map_param

    assert map_param("pH") == "ph"
    assert map_param(None) is None
