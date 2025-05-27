import os
import tempfile
from pathlib import Path
from datetime import date, datetime

import pytest

flask = pytest.importorskip("flask")

import config
from app.quest_box import utils
from app import utils as app_utils
from app.resoconto import utils as resoconto_utils
from app.intrattenimento import utils as intra_utils
from app.calendario import utils as calendario_utils
import run


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.QUEST_BOX_FILE = os.path.join(_tmpdir.name, "quests.json")
    utils.QUESTS_PATH = Path(config.QUEST_BOX_FILE)
    config.COMMENTS_FILE = os.path.join(_tmpdir.name, "comments.json")
    app_utils.COMMENTS_PATH = Path(config.COMMENTS_FILE)


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


def test_show_points_graph_cli(tmp_path, capsys):
    """ポイント履歴サマリ表示の確認"""

    config.POINTS_HISTORY_FILE = os.path.join(tmp_path, "hist.json")
    app_utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)

    ts1 = datetime(2023, 1, 1, 10, 0, 0)
    ts2 = datetime(2023, 1, 2, 10, 0, 0)
    app_utils.log_points_change("u1", 1, 0, ts1)
    app_utils.log_points_change("u1", 2, 0, ts2)

    inputs = iter(["2023-01-01", "2023-01-02"])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.show_points_graph_cli()
    run.input = old_input

    out_lines = capsys.readouterr().out.strip().splitlines()
    assert "2023-01-01 A:1 O:0" in out_lines[0]
    assert "2023-01-02 A:2 O:0" in out_lines[1]


def test_show_resoconto_cli_filtered(capsys):
    resoconto_utils.save_reports([])
    resoconto_utils.add_report("u1", date(2030, 1, 1), "a")
    resoconto_utils.add_report("u2", date(2030, 1, 2), "b")

    user = {"username": "admin", "role": "admin", "email": "a@example.com"}
    inputs = iter(["u2", "2030-01-02", "2030-01-03"])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.show_resoconto(user)
    run.input = old_input

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    assert "u2" in lines[0]


def test_show_resoconto_analysis_cli(capsys):
    resoconto_utils.save_reports([])
    resoconto_utils.add_report("u1", date(2031, 1, 1), "short")
    resoconto_utils.add_report("u2", date(2031, 1, 2), "word " * 25)

    run.show_resoconto_analysis_cli()
    out = capsys.readouterr().out
    assert "u1" in out
    assert "u2" in out


def test_show_intrattenimento_cli_date_filter(capsys):
    config.INTRATTENIMENTO_FILE = os.path.join(_tmpdir.name, "intra.json")
    intra_utils.INTRATTENIMENTO_PATH = Path(config.INTRATTENIMENTO_FILE)
    intra_utils.save_posts([])
    intra_utils.add_post("admin", "old", "b")
    posts = intra_utils.load_posts()
    posts[0]["timestamp"] = (
        datetime(2030, 1, 1, 10, 0, 0)
    ).isoformat(timespec="seconds")
    intra_utils.save_posts(posts)
    intra_utils.add_post("admin", "new", "b")

    user = {"username": "admin", "role": "admin", "email": "a@example.com"}
    inputs = iter(["", "", "2030-01-02", "2030-01-03", "n"])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.show_intrattenimento(user)
    run.input = old_input

    out = capsys.readouterr().out
    assert "new" in out
    assert "old" not in out


def test_comment_post_cli(capsys):
    app_utils.save_posts([])
    app_utils.add_post("u1", "c", "b")
    post_id = app_utils.load_posts()[0]["id"]

    inputs = iter([str(post_id), "good"])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.comment_post_cli({"username": "u2", "role": "user", "email": "u2@example.com"})
    run.input = old_input

    out = capsys.readouterr().out
    assert "投稿しました" in out
    comments = app_utils.get_comments(post_id)
    assert comments[0]["text"] == "good"


def test_edit_calendario_rules_cli(tmp_path, capsys):
    config.CALENDAR_RULES_FILE = os.path.join(tmp_path, "rules.json")
    calendario_utils.RULES_PATH = Path(config.CALENDAR_RULES_FILE)
    calendario_utils.save_rules(calendario_utils.DEFAULT_RULES.copy())

    inputs = iter([
        "6",  # max days
        "2",  # min staff
        "taro-hanako,alice-bob",  # forbidden pairs
        "alice-bob",  # required pairs
        "taro:A,hanako:B",  # employee attributes
        "A:1,B:2",  # required attributes
    ])

    def fake_input(prompt=""):
        return next(inputs)

    old_input = run.input
    run.input = fake_input
    run.edit_calendario_rules()
    run.input = old_input

    out = capsys.readouterr().out
    assert "保存しました" in out

    rules = calendario_utils.load_rules()
    assert rules["max_consecutive_days"] == 6
    assert rules["min_staff_per_day"] == 2
    assert ["taro", "hanako"] in rules["forbidden_pairs"]
    assert ["alice", "bob"] in rules["required_pairs"]
    assert rules["employee_attributes"]["taro"] == "A"
    assert rules["required_attributes"]["B"] == 2
