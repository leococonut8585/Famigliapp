import getpass
from typing import Dict
from datetime import datetime

from app import utils
from app.intrattenimento import utils as intrattenimento_utils


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
        print("12. 履歴をCSV出力")
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
            export_history_csv()
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
    posts = utils.filter_posts(category=category, author=author, keyword=keyword)
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


def main():
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
