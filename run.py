import getpass
import os
import shutil
import json
from typing import Dict
from datetime import datetime

from app import utils
from app.intrattenimento import utils as intrattenimento_utils
from app.corso import utils as corso_utils
from app.resoconto import utils as resoconto_utils
from app.resoconto.tasks import start_scheduler
from app.principessina import utils as principessina_utils
from app.quest_box import utils as quest_utils
from app.lezzione import utils as lezzione_utils
from app.bravissimo import utils as bravissimo_utils
from app.scatola_capriccio import utils as scatola_capriccio_utils
from app.monsignore import utils as monsignore_utils
from app.calendario import utils as calendario_utils


def display_menu(user: Dict[str, str]):
    while True:
        print("\n--- Famigliapp Menu ---")
        print("1. ポイントを見る")
        if user["role"] == "admin":
            print("2. ポイントを編集する")
        print("3. 投稿を見る")
        print("4. 投稿する")
        if user["role"] == "admin":
            print("5. 投稿を削除する")
        print("6. ランキングを見る")
        print("7. ポイント履歴を見る")
        print("8. 投稿を編集する")
        print("9. intrattenimento を見る")
        print("10. intrattenimento に投稿する")
        if user["role"] == "admin":
            print("11. intrattenimento 投稿を削除する")
        print("12. Corso を見る")
        print("13. Corso に投稿する")
        print("14. 履歴をCSV出力")
        print("15. Resoconto を見る")
        print("16. Resoconto に投稿する")
        if user["role"] == "admin":
            print("17. Resoconto ランキングを見る")
        print("18. Principessina を見る")
        print("19. Principessina に投稿する")
        print("20. Quest一覧を見る")
        print("21. Questを投稿する")
        print("22. QuestをAcceptする")
        print("23. Questを完了する")
        if user["role"] == "admin":
            print("24. Questを削除する")
            print("25. Quest報酬を設定する")
        print("26. Lezzione一覧を見る")
        print("27. Lezzioneをスケジュールする")
        print("28. Lezzioneにフィードバックする")
        print("29. Bravissimo を見る")
        if user["role"] == "admin":
            print("30. Bravissimo に投稿する")
            print("31. Bravissimo 投稿を削除する")
        if user["role"] == "admin":
            print("32. Scatola Capriccio を見る")
        print("33. Scatola Capriccio に投稿する")
        print("34. Monsignore を見る")
        print("35. Monsignore に投稿する")
        if user["role"] == "admin":
            print("36. Monsignore 投稿を削除する")
        print("37. カレンダーを見る")
        print("38. カレンダーにイベント追加")
        if user["role"] == "admin":
            print("39. カレンダーのイベント削除")
        print("40. カレンダーのイベント移動")
        print("41. カレンダーの担当者割当")
        if user["role"] == "admin":
            print("42. カレンダールールを見る")
            print("43. カレンダールールを編集する")
            print("44. Questを編集する")
            print("45. ResocontoをCSV出力")
        print("46. カレンダー統計を見る")
        print("0. 終了")
        choice = input("選択してください: ")
        if choice == "1":
            show_points(user)
        elif choice == "2":
            if user["role"] == "admin":
                edit_points()
            else:
                print("権限がありません")
        elif choice == "3":
            show_posts()
        elif choice == "4":
            add_post(user)
        elif choice == "5":
            if user["role"] == "admin":
                remove_post()
            else:
                print("権限がありません")
        elif choice == "6":
            show_ranking()
        elif choice == "7":
            show_points_history()
        elif choice == "8":
            edit_post_cli(user)
        elif choice == "9":
            show_intrattenimento(user)
        elif choice == "10":
            add_intrattenimento_post(user)
        elif choice == "11":
            if user["role"] == "admin":
                delete_intrattenimento_post()
            else:
                print("権限がありません")
        elif choice == "12":
            show_corso(user)
        elif choice == "13":
            add_corso_post(user)
        elif choice == "14":
            export_history_csv()
        elif choice == "15":
            show_resoconto(user)
        elif choice == "16":
            add_resoconto(user)
        elif choice == "17":
            if user["role"] == "admin":
                show_resoconto_ranking()
            else:
                print("権限がありません")
        elif choice == "18":
            show_principessina(user)
        elif choice == "19":
            add_principessina_post(user)
        elif choice == "20":
            show_quests()
        elif choice == "21":
            add_quest_cli(user)
        elif choice == "22":
            accept_quest_cli(user)
        elif choice == "23":
            complete_quest_cli(user)
        elif choice == "24":
            if user["role"] == "admin":
                delete_quest_cli()
            else:
                print("権限がありません")
        elif choice == "25":
            if user["role"] == "admin":
                set_quest_reward_cli()
            else:
                print("権限がありません")
        elif choice == "26":
            show_lezzione_entries(user)
        elif choice == "27":
            schedule_lezzione(user)
        elif choice == "28":
            add_lezzione_feedback_cli(user)
        elif choice == "29":
            show_bravissimo_posts(user)
        elif choice == "30":
            if user["role"] == "admin":
                add_bravissimo_post(user)
            else:
                print("権限がありません")
        elif choice == "31":
            if user["role"] == "admin":
                delete_bravissimo_post()
            else:
                print("権限がありません")
        elif choice == "32":
            if user["role"] == "admin":
                show_scatola_capriccio_posts(user)
            else:
                print("権限がありません")
        elif choice == "33":
            add_scatola_capriccio_post(user)
        elif choice == "34":
            show_monsignore_posts(user)
        elif choice == "35":
            add_monsignore_post(user)
        elif choice == "36":
            if user["role"] == "admin":
                delete_monsignore_post()
            else:
                print("権限がありません")
        elif choice == "37":
            show_calendario_events()
        elif choice == "38":
            add_calendario_event(user)
        elif choice == "39":
            if user["role"] == "admin":
                delete_calendario_event()
            else:
                print("権限がありません")
        elif choice == "40":
            move_calendario_event()
        elif choice == "41":
            assign_calendario_employee()
        elif choice == "42":
            if user["role"] == "admin":
                show_calendario_rules()
            else:
                print("権限がありません")
        elif choice == "43":
            if user["role"] == "admin":
                edit_calendario_rules()
            else:
                print("権限がありません")
        elif choice == "44":
            if user["role"] == "admin":
                edit_quest_cli()
            else:
                print("権限がありません")
        elif choice == "45":
            if user["role"] == "admin":
                export_resoconto_csv()
            else:
                print("権限がありません")
        elif choice == "46":
            show_calendario_stats()
        elif choice == "0":
            break
        else:
            print("無効な選択です")


def show_points(user: Dict[str, str]):
    points = utils.load_points()
    if user["role"] == "admin":
        for username, p in points.items():
            print(
                f"{username}: A={p.get('A',0)} O={p.get('O',0)} U={p.get('A',0)-p.get('O',0)}"
            )
    else:
        p = points.get(user["username"], {"A": 0, "O": 0})
        print(f"A={p.get('A',0)} O={p.get('O',0)} U={p.get('A',0)-p.get('O',0)}")


def edit_points():
    username = input("編集するユーザー名: ")
    points = utils.load_points()
    if username not in points:
        points[username] = {"A": 0, "O": 0}
    try:
        a = int(input("Aポイント: "))
        o = int(input("Oポイント: "))
    except ValueError:
        print("数値を入力してください")
        return
    old_a = points[username].get("A", 0)
    old_o = points[username].get("O", 0)
    points[username]["A"] = a
    points[username]["O"] = o
    utils.save_points(points)
    utils.log_points_change(username, a - old_a, o - old_o)
    print("保存しました")


def show_posts():
    category = input("カテゴリ(空欄は全て): ").strip()
    author = input("投稿者(空欄は全て): ").strip()
    keyword = input("検索語(空欄は全て): ").strip()
    start_s = input("開始日 YYYY-MM-DD(空欄は指定なし): ").strip()
    end_s = input("終了日 YYYY-MM-DD(空欄は指定なし): ").strip()
    start = end = None
    try:
        if start_s:
            start = datetime.strptime(start_s, "%Y-%m-%d")
        if end_s:
            end = datetime.strptime(end_s, "%Y-%m-%d")
    except ValueError:
        print("日付の形式が正しくありません")
        return
    posts = utils.filter_posts(
        category=category,
        author=author,
        keyword=keyword,
        start=start,
        end=end,
    )
    for p in posts:
        print(f"[{p['id']}] {p['timestamp']} {p['author']} {p['category']} {p['text']}")


def add_post(user: Dict[str, str]):
    category = input("カテゴリ: ").strip()
    text = input("内容: ").strip()
    if not text:
        print("内容が空です")
        return
    utils.add_post(user["username"], category, text)
    print("投稿しました")


def remove_post():
    try:
        post_id = int(input("削除するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if utils.delete_post(post_id):
        print("削除しました")
    else:
        print("該当IDがありません")


def edit_post_cli(user: Dict[str, str]):
    try:
        post_id = int(input("編集するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    posts = utils.load_posts()
    post = next((p for p in posts if p.get("id") == post_id), None)
    if not post:
        print("該当IDがありません")
        return
    if user["role"] != "admin" and user["username"] != post.get("author"):
        print("権限がありません")
        return

    category = input(f"カテゴリ[{post.get('category','')}] : ").strip() or post.get("category", "")
    text = input(f"内容[{post.get('text','')}] : ").strip() or post.get("text", "")
    if not text:
        print("内容が空です")
        return
    utils.update_post(post_id, category, text)
    print("更新しました")


def show_ranking():
    metric = input("ランキング種別を選択 (A/O/U): ").strip().upper()
    if metric not in {"A", "O", "U"}:
        print("A, O, U のいずれかを入力してください")
        return
    period = input("期間を指定 (all/weekly/monthly/yearly/custom): ").strip().lower()
    start = end = None
    kwargs = {}
    if period == "weekly":
        kwargs["period"] = "weekly"
    elif period == "monthly":
        kwargs["period"] = "monthly"
    elif period == "yearly":
        kwargs["period"] = "yearly"
    elif period == "custom":
        s = input("開始日 YYYY-MM-DD: ").strip()
        e = input("終了日 YYYY-MM-DD: ").strip()
        try:
            start = datetime.strptime(s, "%Y-%m-%d") if s else None
            end = datetime.strptime(e, "%Y-%m-%d") if e else None
            kwargs["start"] = start
            kwargs["end"] = end
        except ValueError:
            print("日付の形式が正しくありません")
            return
    ranking = utils.get_ranking(metric, **kwargs)
    for i, (user, value) in enumerate(ranking, 1):
        print(f"{i}. {user}: {value}")


def show_points_history():
    username = input("ユーザー名(空欄は全員): ").strip()
    start_s = input("開始日 YYYY-MM-DD(空欄は指定なし): ").strip()
    end_s = input("終了日 YYYY-MM-DD(空欄は指定なし): ").strip()

    start = end = None
    try:
        if start_s:
            start = datetime.strptime(start_s, "%Y-%m-%d")
        if end_s:
            end = datetime.strptime(end_s, "%Y-%m-%d")
    except ValueError:
        print("日付の形式が正しくありません")
        return

    history = utils.filter_points_history(start=start, end=end, username=username)
    for entry in history:
        ts = entry.get("timestamp")
        user = entry.get("username")
        delta_a = entry.get("A", 0)
        delta_o = entry.get("O", 0)
        print(f"{ts} {user} A:{delta_a:+d} O:{delta_o:+d}")


def export_history_csv() -> None:
    """Prompt for a path and export points history to CSV."""

    path = input("出力先CSVファイル: ").strip()
    if not path:
        print("ファイル名を入力してください")
        return
    utils.export_points_history_csv(path)
    print("エクスポートしました")


def show_intrattenimento(user: Dict[str, str]) -> None:
    author = input("投稿者(空欄は全て): ").strip()
    keyword = input("検索語(空欄は全て): ").strip()
    include_expired = False
    if user["role"] == "admin":
        incl = input("公開終了済みも表示？(y/N): ").strip().lower()
        include_expired = incl == "y"
    posts = intrattenimento_utils.filter_posts(
        author=author, keyword=keyword, include_expired=include_expired
    )
    for p in posts:
        end = p.get("end_date", "")
        print(
            f"[{p['id']}] {p['timestamp']} {p['author']} {p.get('title','')} {end} {p.get('body','')}"
        )


def add_intrattenimento_post(user: Dict[str, str]) -> None:
    title = input("タイトル: ").strip()
    body = input("本文: ").strip()
    end_s = input("公開終了日 YYYY-MM-DD(空欄はなし): ").strip()
    end_date = None
    if end_s:
        try:
            end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
        except ValueError:
            print("日付の形式が正しくありません")
            return
    intrattenimento_utils.add_post(user["username"], title, body, end_date)
    print("投稿しました")


def delete_intrattenimento_post() -> None:
    try:
        post_id = int(input("削除するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if intrattenimento_utils.delete_post(post_id):
        print("削除しました")
    else:
        print("該当IDがありません")


def show_corso(user: Dict[str, str]) -> None:
    author = input("投稿者(空欄は全て): ").strip()
    keyword = input("検索語(空欄は全て): ").strip()
    include_expired = False
    if user["role"] == "admin":
        incl = input("公開終了済みも表示？(y/N): ").strip().lower()
        include_expired = incl == "y"
    posts = corso_utils.filter_posts(
        author=author, keyword=keyword, include_expired=include_expired
    )
    for p in posts:
        end = p.get("end_date", "")
        print(
            f"[{p['id']}] {p['timestamp']} {p['author']} {p.get('title','')} {end} {p.get('body','')}"
        )


def add_corso_post(user: Dict[str, str]) -> None:
    title = input("タイトル: ").strip()
    body = input("本文: ").strip()
    end_s = input("公開終了日 YYYY-MM-DD(空欄はなし): ").strip()
    end_date = None
    if end_s:
        try:
            end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
        except ValueError:
            print("日付の形式が正しくありません")
            return
    corso_utils.add_post(user["username"], title, body, end_date)
    print("投稿しました")


def show_resoconto(user: Dict[str, str]) -> None:
    reports = resoconto_utils.load_reports()
    if user["role"] == "admin":
        for r in reports:
            print(f"[{r['id']}] {r['date']} {r['author']} {r['body']}")
    else:
        for r in reports:
            if r.get("author") == user["username"]:
                print(f"[{r['id']}] {r['date']} {r['body']}")


def add_resoconto(user: Dict[str, str]) -> None:
    date_s = input("日付 YYYY-MM-DD: ").strip()
    body = input("内容: ").strip()
    try:
        d = datetime.strptime(date_s, "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式が正しくありません")
        return
    resoconto_utils.add_report(user["username"], d, body)
    print("投稿しました")


def show_resoconto_ranking() -> None:
    start_s = input("開始日 YYYY-MM-DD(空欄は指定なし): ").strip()
    end_s = input("終了日 YYYY-MM-DD(空欄は指定なし): ").strip()
    start = end = None
    try:
        if start_s:
            start = datetime.strptime(start_s, "%Y-%m-%d").date()
        if end_s:
            end = datetime.strptime(end_s, "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式が正しくありません")
        return
    ranking = resoconto_utils.get_ranking(start=start, end=end)
    for i, (user, count) in enumerate(ranking, 1):
        print(f"{i}. {user}: {count}")


def export_resoconto_csv() -> None:
    """ResocontoデータをCSVに出力する。"""

    path = input("出力先CSVファイル: ").strip()
    if not path:
        print("ファイル名を入力してください")
        return
    resoconto_utils.export_reports_csv(path)
    print("エクスポートしました")


def show_principessina(user: Dict[str, str]) -> None:
    author = input("投稿者(空欄は全て): ").strip()
    keyword = input("検索語(空欄は全て): ").strip()
    posts = principessina_utils.filter_posts(author=author, keyword=keyword)
    for p in posts:
        print(f"[{p['id']}] {p['timestamp']} {p['author']} {p.get('body','')}")


def add_principessina_post(user: Dict[str, str]) -> None:
    body = input("本文: ").strip()
    if not body:
        print("内容が空です")
        return
    principessina_utils.add_post(user["username"], body)
    print("投稿しました")


def show_quests() -> None:
    quests = quest_utils.load_quests()
    for q in quests:
        due = f" (期限: {q['due_date']})" if q.get("due_date") else ""
        assignee = f" (対象: {q['assigned_to']})" if q.get('assigned_to') else ""
        print(
            f"[{q['id']}] {q['title']}{due}{assignee} {q['author']} {q['status']} {q.get('accepted_by','')} {q.get('reward','')}"
        )


def add_quest_cli(user: Dict[str, str]) -> None:
    title = input("タイトル: ").strip()
    body = input("内容: ").strip()
    due_s = input("期限 YYYY-MM-DD(空欄はなし): ").strip()
    assigned_to = input("対象ユーザー(空欄はなし): ").strip()
    due_date = None
    if due_s:
        try:
            due_date = datetime.strptime(due_s, "%Y-%m-%d").date()
        except ValueError:
            print("日付の形式が正しくありません")
            return
    quest_utils.add_quest(user["username"], title, body, due_date, assigned_to)
    print("投稿しました")


def accept_quest_cli(user: Dict[str, str]) -> None:
    try:
        quest_id = int(input("AcceptするID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if quest_utils.accept_quest(quest_id, user["username"]):
        print("Acceptしました")
    else:
        print("操作できません")


def complete_quest_cli(user: Dict[str, str]) -> None:
    try:
        quest_id = int(input("完了するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if quest_utils.complete_quest(quest_id):
        print("完了しました")
    else:
        print("操作できません")


def delete_quest_cli() -> None:
    try:
        quest_id = int(input("削除するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if quest_utils.delete_quest(quest_id):
        print("削除しました")
    else:
        print("該当IDがありません")


def set_quest_reward_cli() -> None:
    try:
        quest_id = int(input("報酬を設定するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    reward = input("報酬: ").strip()
    if quest_utils.set_reward(quest_id, reward):
        print("保存しました")
    else:
        print("該当IDがありません")


def edit_quest_cli() -> None:
    """Edit an existing quest entry."""
    try:
        quest_id = int(input("編集するID: "))
    except ValueError:
        print("数値を入力してください")
        return

    quests = quest_utils.load_quests()
    quest = next((q for q in quests if q.get("id") == quest_id), None)
    if not quest:
        print("該当IDがありません")
        return

    title = input(f"タイトル[{quest.get('title','')}] : ").strip() or quest.get("title", "")
    body = input(f"内容[{quest.get('body','')}] : ").strip() or quest.get("body", "")
    due_s = input(
        f"期限 YYYY-MM-DD[{quest.get('due_date','')}] : "
    ).strip() or quest.get("due_date", "")
    assigned_to = (
        input(f"対象ユーザー[{quest.get('assigned_to','')}] : ").strip()
        or quest.get("assigned_to", "")
    )

    due_date = None
    if due_s:
        try:
            due_date = datetime.strptime(due_s, "%Y-%m-%d").date()
        except ValueError:
            print("日付の形式が正しくありません")
            return

    if quest_utils.update_quest(quest_id, title, body, due_date, assigned_to):
        print("更新しました")
    else:
        print("該当IDがありません")


def show_lezzione_entries(user: Dict[str, str]) -> None:
    entries = lezzione_utils.load_entries()
    for e in entries:
        if user["role"] != "admin" and e.get("author") != user["username"]:
            continue
        print(
            f"[{e['id']}] {e['lesson_date']} {e['author']} {e['title']} {e.get('feedback','')}")
    

def schedule_lezzione(user: Dict[str, str]) -> None:
    date_s = input("日付 YYYY-MM-DD: ").strip()
    title = input("タイトル: ").strip()
    try:
        d = datetime.strptime(date_s, "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式が正しくありません")
        return
    lezzione_utils.add_schedule(user["username"], d, title)
    print("登録しました")


def add_lezzione_feedback_cli(user: Dict[str, str]) -> None:
    try:
        entry_id = int(input("フィードバックするID: "))
    except ValueError:
        print("数値を入力してください")
        return
    entries = lezzione_utils.load_entries()
    entry = next((e for e in entries if e.get("id") == entry_id), None)
    if not entry:
        print("該当IDがありません")
        return
    if user["role"] != "admin" and entry.get("author") != user["username"]:
        print("権限がありません")
        return
    body = input("内容: ").strip()
    if lezzione_utils.add_feedback(entry_id, body):
        print("投稿しました")
    else:
        print("該当IDがありません")


def show_bravissimo_posts(user: Dict[str, str]) -> None:
    author = input("投稿者(空欄は全て): ").strip()
    keyword = input("検索語(空欄は全て): ").strip()
    posts = bravissimo_utils.filter_posts(author=author, keyword=keyword)
    for p in posts:
        fname = p.get("filename", "")
        text = p.get("text", p.get("body", ""))
        print(f"[{p['id']}] {p['timestamp']} {p['author']} {fname} {text}")


def add_bravissimo_post(user: Dict[str, str]) -> None:
    text = input("内容: ").strip()
    audio = input("音声ファイルパス(空欄はなし): ").strip()
    filename = None
    if audio:
        os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
        fname = os.path.basename(audio)
        dest = os.path.join("static", "uploads", fname)
        try:
            shutil.copy(audio, dest)
            filename = fname
        except Exception as e:
            print("ファイルを保存できません", e)
            return
    bravissimo_utils.add_post(user["username"], text, filename)
    print("投稿しました")


def delete_bravissimo_post() -> None:
    try:
        post_id = int(input("削除するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if bravissimo_utils.delete_post(post_id):
        print("削除しました")
    else:
        print("該当IDがありません")


def show_scatola_capriccio_posts(user: Dict[str, str]) -> None:
    posts = scatola_capriccio_utils.load_posts()
    for p in posts:
        print(f"[{p['id']}] {p['timestamp']} {p['author']} {p.get('body','')}")


def add_scatola_capriccio_post(user: Dict[str, str]) -> None:
    body = input("内容: ").strip()
    if not body:
        print("内容が空です")
        return
    scatola_capriccio_utils.add_post(user["username"], body)
    print("投稿しました")


def show_monsignore_posts(user: Dict[str, str]) -> None:
    author = input("投稿者(空欄は全て): ").strip()
    keyword = input("検索語(空欄は全て): ").strip()
    posts = monsignore_utils.filter_posts(author=author, keyword=keyword)
    for p in posts:
        fname = p.get("filename", "")
        print(
            f"[{p['id']}] {p['timestamp']} {p['author']} {fname} {p.get('body','')}"
        )


def add_monsignore_post(user: Dict[str, str]) -> None:
    body = input("本文: ").strip()
    img = input("画像ファイルパス(空欄はなし): ").strip()
    filename = None
    if img:
        os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
        fname = os.path.basename(img)
        dest = os.path.join("static", "uploads", fname)
        try:
            shutil.copy(img, dest)
            filename = fname
        except Exception as e:
            print("ファイルを保存できません", e)
            return
    monsignore_utils.add_post(user["username"], body, filename)
    print("投稿しました")


def delete_monsignore_post() -> None:
    try:
        post_id = int(input("削除するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if monsignore_utils.delete_post(post_id):
        print("削除しました")
    else:
        print("該当IDがありません")


def show_calendario_events() -> None:
    events = calendario_utils.load_events()
    events.sort(key=lambda e: e.get("date"))
    for e in events:
        print(
            f"[{e['id']}] {e['date']} {e['title']} {e.get('employee','')} {e.get('description','')}"
        )


def add_calendario_event(user: Dict[str, str]) -> None:
    date_s = input("日付 YYYY-MM-DD: ").strip()
    title = input("タイトル: ").strip()
    description = input("説明: ").strip()
    employee = input("担当者: ").strip()
    try:
        d = datetime.strptime(date_s, "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式が正しくありません")
        return
    calendario_utils.add_event(d, title, description, employee)
    print("追加しました")


def delete_calendario_event() -> None:
    try:
        event_id = int(input("削除するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    if calendario_utils.delete_event(event_id):
        print("削除しました")
    else:
        print("該当IDがありません")


def move_calendario_event() -> None:
    try:
        event_id = int(input("移動するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    date_s = input("新しい日付 YYYY-MM-DD: ").strip()
    try:
        new_date = datetime.strptime(date_s, "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式が正しくありません")
        return
    if calendario_utils.move_event(event_id, new_date):
        print("移動しました")
    else:
        print("該当IDがありません")


def assign_calendario_employee() -> None:
    try:
        event_id = int(input("担当を設定するID: "))
    except ValueError:
        print("数値を入力してください")
        return
    employee = input("担当者: ").strip()
    if calendario_utils.assign_employee(event_id, employee):
        print("更新しました")
    else:
        print("該当IDがありません")


def show_calendario_stats() -> None:
    """Display work/off day counts for each employee."""

    start_s = input("開始日 YYYY-MM-DD(空欄は指定なし): ").strip()
    end_s = input("終了日 YYYY-MM-DD(空欄は指定なし): ").strip()
    start = end = None
    try:
        if start_s:
            start = datetime.strptime(start_s, "%Y-%m-%d").date()
        if end_s:
            end = datetime.strptime(end_s, "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式が正しくありません")
        return

    stats = calendario_utils.compute_employee_stats(start=start, end=end)
    for emp, data in stats.items():
        line = f"{emp}: 勤務日数 {data['work_days']}"
        off = data.get("off_days")
        if off is not None:
            line += f" 休日数 {off}"
        print(line)


def show_calendario_rules() -> None:
    """現在のカレンダー運用ルールを表示する。"""
    rules = calendario_utils.load_rules()
    print(json.dumps(rules, ensure_ascii=False, indent=2))


def edit_calendario_rules() -> None:
    """主要なカレンダールールを編集する。"""
    rules = calendario_utils.load_rules()
    try:
        max_days = input(
            f"連勤最大日数[{rules.get('max_consecutive_days', 5)}]: "
        ).strip()
        if max_days:
            rules['max_consecutive_days'] = int(max_days)
        min_staff = input(
            f"最低人数[{rules.get('min_staff_per_day', 1)}]: "
        ).strip()
        if min_staff:
            rules['min_staff_per_day'] = int(min_staff)
    except ValueError:
        print("数値を入力してください")
        return
    calendario_utils.save_rules(rules)
    print("保存しました")

def main():
    start_scheduler()
    username = input("ユーザー名: ")
    password = getpass.getpass("パスワード: ")
    user = utils.login(username, password)
    if not user:
        print("ログイン失敗")
        return
    print(f"{username}でログインしました")
    display_menu(user)


if __name__ == "__main__":
    main()
