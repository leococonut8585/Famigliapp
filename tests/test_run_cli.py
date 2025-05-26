import os
import tempfile
from pathlib import Path
from datetime import date

import pytest

flask = pytest.importorskip("flask")

import config
from app.quest_box import utils
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
