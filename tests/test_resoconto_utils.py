import os
import tempfile
from pathlib import Path
from datetime import date

import config
import pytest

flask = pytest.importorskip("flask")
from app.resoconto import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.RESOCONTO_FILE = os.path.join(_tmpdir.name, "resoconto.json")
    utils.REPORTS_PATH = Path(config.RESOCONTO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_get_ranking():
    utils.add_report("u1", date.fromisoformat("2025-01-01"), "a")
    utils.add_report("u2", date.fromisoformat("2025-01-02"), "b")
    utils.add_report("u1", date.fromisoformat("2025-01-03"), "c")
    ranking = utils.get_ranking()
    assert ranking[0][0] == "u1" and ranking[0][1] == 2
    assert ranking[1][0] == "u2" and ranking[1][1] == 1


def test_filter_reports():
    utils.save_reports([])
    utils.add_report("u1", date.fromisoformat("2025-01-05"), "a")
    utils.add_report("u2", date.fromisoformat("2025-01-10"), "b")
    start = date.fromisoformat("2025-01-07")
    end = date.fromisoformat("2025-01-15")
    res = utils.filter_reports(author="u2", start=start, end=end)
    assert len(res) == 1
    assert res[0]["author"] == "u2"
