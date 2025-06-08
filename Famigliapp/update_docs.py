#!/usr/bin/env python3
"""開発ドキュメントの更新補助スクリプト"""

import os
import json
from datetime import datetime
from pathlib import Path

def update_project_status():
    """PROJECT_STATUS.mdの最終更新日時を自動更新"""
    status_file = Path("DEVELOPMENT_DOCS/PROJECT_STATUS.md")
    if status_file.exists():
        content = status_file.read_text(encoding='utf-8')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Ensure the placeholder exists before replacing
        placeholder = "最終更新: [自動で日時を挿入]"
        if placeholder in content:
            updated_content = content.replace(
                placeholder,
                f"最終更新: {now}"
            )
        else:
            # If placeholder is not found, try to find any existing timestamp
            import re
            # This regex looks for "最終更新: " followed by a date/time string
            # and replaces it, or prepends if not found at all.
            match = re.search(r"最終更新: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)
            if match:
                updated_content = re.sub(r"最終更新: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", f"最終更新: {now}", content)
            else:
                # If no timestamp is found, add it at the beginning of the file or after the title
                title_match = re.search(r"^# Famigliapp プロジェクトステータス
", content, re.MULTILINE)
                if title_match:
                    insert_pos = title_match.end()
                    updated_content = content[:insert_pos] + f"最終更新: {now}

" + content[insert_pos:]
                else: # Prepend if title not found
                    updated_content = f"最終更新: {now}

" + content

        status_file.write_text(updated_content, encoding='utf-8')
        print(f"PROJECT_STATUS.md を更新しました: {now}")
    else:
        print(f"エラー: {status_file} が見つかりません。")

def create_session_log_template(session_number: int, user_name: str = "[ユーザー名]", assistant_name: str = "[Claude/Jules等]"):
    """新規セッションログファイルのテンプレート内容を生成"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    template = f"""# セッション{session_number:03d} - {date_str}

## 参加者
- ユーザー: {user_name}
- アシスタント: {assistant_name}

## 議論内容
### 主要トピック
- [トピック1]
- [トピック2]

### 決定事項
- [決定1]
- [決定2]

## 作成物
- [ファイル名1](path/to/file1)
- [機能名1]

## 次回への申し送り事項
- [申し送り1]
- [申し送り2]

## コード変更
\`\`\`diff
# 主要な変更箇所のサンプル
# file: path/to/changed_file.py
# def example_function():
# -    old_code
# +    new_code
\`\`\`
"""
    return template

def create_new_session_log(session_number: int, user_name: str = "[ユーザー名]", assistant_name: str = "[Claude/Jules等]"):
    """新規セッションログファイルを作成"""
    logs_dir = Path("DEVELOPMENT_DOCS/CONVERSATION_LOGS")
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        print(f"ディレクトリを作成しました: {logs_dir}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"session_{session_number:03d}_{date_str}.md"
    file_path = logs_dir / filename

    log_content = create_session_log_template(session_number, user_name, assistant_name)

    file_path.write_text(log_content, encoding='utf-8')
    print(f"作成: {file_path}")

def get_next_session_number():
    """次のセッション番号を自動で決定"""
    logs_dir = Path("DEVELOPMENT_DOCS/CONVERSATION_LOGS")
    if not logs_dir.exists():
        return 1

    max_session_num = 0
    for f in logs_dir.glob("session_*.md"):
        try:
            num_part = f.name.split('_')[1]
            session_num = int(num_part)
            if session_num > max_session_num:
                max_session_num = session_num
        except (IndexError, ValueError):
            # ファイル名が期待するフォーマットでない場合はスキップ
            continue
    return max_session_num + 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="開発ドキュメント管理スクリプト")
    parser.add_argument(
        "--update-status",
        action="store_true",
        help="PROJECT_STATUS.mdの最終更新日時を更新します。"
    )
    parser.add_argument(
        "--new-log",
        action="store_true",
        help="新しいセッションログファイルを作成します。自動で次のセッション番号が採番されます。"
    )
    parser.add_argument(
        "--session-number",
        type=int,
        help="新しいセッションログの番号を指定します (オプション)。指定しない場合は自動採番。"
    )
    parser.add_argument(
        "--user",
        type=str,
        default="[ユーザー名]",
        help="セッションログに記載するユーザー名を指定します。"
    )
    parser.add_argument(
        "--assistant",
        type=str,
        default="[AI Assistant]",
        help="セッションログに記載するアシスタント名を指定します。"
    )

    args = parser.parse_args()

    if args.update_status:
        update_project_status()

    if args.new_log:
        session_num_to_use = args.session_number if args.session_number is not None else get_next_session_number()
        create_new_session_log(session_num_to_use, args.user, args.assistant)
        # SUMMARY.mdにも追記する機能もここに追加できると良い
        # 例: update_summary(session_num_to_use, date_str)

    if not (args.update_status or args.new_log):
        parser.print_help()
        print("\nオプションを指定して実行してください。")
        print("例: python update_docs.py --update-status --new-log --user "坂口烈緒" --assistant "Jules"")
