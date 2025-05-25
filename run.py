import getpass
from typing import Dict

from app import utils



def display_menu(user: Dict[str, str]):
    while True:
        print("\n--- Famigliapp Punto Menu ---")
        print("1. ポイントを見る")
        if user['role'] == 'admin':
            print("2. ポイントを編集する")
        print("0. 終了")
        choice = input("選択してください: ")
        if choice == '1':
            show_points(user)
        elif choice == '2' and user['role'] == 'admin':
            edit_points()
        elif choice == '0':
            break
        else:
            print("無効な選択です")


def show_points(user: Dict[str, str]):
    points = utils.load_points()
    if user['role'] == 'admin':
        for username, p in points.items():
            print(f"{username}: A={p.get('A',0)} O={p.get('O',0)} U={p.get('A',0)-p.get('O',0)}")
    else:
        p = points.get(user['username'], {'A': 0, 'O': 0})
        print(f"A={p.get('A',0)} O={p.get('O',0)} U={p.get('A',0)-p.get('O',0)}")


def edit_points():
    username = input("編集するユーザー名: ")
    points = utils.load_points()
    if username not in points:
        points[username] = {'A': 0, 'O': 0}
    try:
        a = int(input("Aポイント: "))
        o = int(input("Oポイント: "))
    except ValueError:
        print("数値を入力してください")
        return
    points[username]['A'] = a
    points[username]['O'] = o
    utils.save_points(points)
    print("保存しました")


def main():
    username = input("ユーザー名: ")
    password = getpass.getpass("パスワード: ")
    user = utils.login(username, password)
    if not user:
        print("ログイン失敗")
        return
    print(f"{username}でログインしました")
    display_menu(user)


if __name__ == '__main__':
    main()
