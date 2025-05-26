import os
import tempfile
from pathlib import Path
from datetime import date

import pytest

flask = pytest.importorskip("flask")

import config
from app.quest_box import utils
from app.resoconto import utils as resoconto_utils
import run


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.QUEST_BOX_FILE = os.path.join(_tmpdir.name, "quests.json")
    utils.QUESTS_PATH = Path(config.QUEST_BOX_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_show_quests_cli(capsys):
    utils.save_quests([])
    utils.add_quest("u1", "t1", "b1", date(2030, 2, 3))
    utils.add_quest("u2", "t2", "b2", None)
    run.show_quests()
    out = capsys.readouterr().out.strip().splitlines()
    assert "(期限: 2030-02-03)" in out[0]
    assert "(期限:" not in out[1]


def test_edit_quest_cli(capsys):
    utils.save_quests([])
    utils.add_quest("u1", "orig", "b", None)
    qid = utils.load_quests()[0]["id"]

    inputs = iter([str(qid), "new", "bb", "2031-01-01", "u2"])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.edit_quest_cli()
    run.input = old_input
    out = capsys.readouterr().out
    assert "更新しました" in out
    q = utils.load_quests()[0]
    assert q["title"] == "new"
    assert q["due_date"] == "2031-01-01"
    assert q["assigned_to"] == "u2"


def test_export_resoconto_csv(tmp_path, capsys):
    resoconto_utils.save_reports([])
    resoconto_utils.add_report("u1", date(2030, 1, 1), "body")
    csv_path = tmp_path / "res.csv"

    inputs = iter([str(csv_path)])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.export_resoconto_csv()
    run.input = old_input

    out = capsys.readouterr().out
    assert "エクスポートしました" in out
    with open(csv_path, "r", encoding="utf-8") as f:
        contents = f.read()
    assert "u1" in contents
