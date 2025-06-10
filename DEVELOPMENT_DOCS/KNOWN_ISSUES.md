# 既知の問題

## 解決した問題 (2025-06-09 Julesセッション対応分)

-   **編集フォームのテンプレートエラー**: イベント編集フォーム (`event_form.html`) で `form.time` が存在しないために発生していたエラー。(`form.start_time`, `form.end_time` に対応することで解決)
-   **日付セルの幅の問題**: カレンダーの日付セルの幅が狭く、イベント内容が見づらかったり、レイアウトが崩れたりする可能性があった問題。(`style.css` でセル幅を `180px` に拡大して解決)
-   **メインカレンダー詳細表示の問題**: 詳細ボタンが反応しない、または古いモーダルUIが表示される問題。(`month_view.html` と `calendar_event_details.js` を修正し、新しいカスタムポップアップ `showCalendarioPopup` で表示するようにして解決)
-   **シフト管理エリアのカレンダー表示範囲の問題**: 表示月に対して前2週間が表示され、月末が表示されないことがあった問題。(`routes.py` の `/shift` ルートの表示期間計算ロジックを修正して解決)
-   **イベントカテゴリのカラー適用不備**: 「出張」や「マミー系」といった特定のイベントカテゴリに意図した背景色・文字色が適用されていなかった問題。(`style.css` の修正、`routes.py` でのカテゴリ名正規化、`month_view.html` での適用方法変更により解決)
-   **シフト管理エリアの警告ポップアップの不統一**: シフト管理機能内で一部 `alert()` が使用されており、他のポップアップと表示スタイルや挙動が異なっていた問題。(`shift_manager.js` を修正し、`showCalendarioPopup` に統一して解決)
-   **Flask起動時のModuleNotFoundError**: `app.seminario` (小文字s) と `app.Seminario` (大文字S) のインポートパスの不一致により、`ModuleNotFoundError: No module named 'app.seminario'` が発生していた問題。(2025-06-09 緊急修正にて `wsgi.py`, `tests/*.py` のパスを `app.Seminario` に統一して解決)

## 解決した問題 (2025-06-09 Julesセッション Calendarioモジュール修正分)

-   **EventForm 'time' 属性エラーの再修正**: `app/calendario/routes.py` の `add` および `edit_event` 関数内で、`form.time` の代わりに `form.start_time` を参照するように修正し、`AttributeError` を解消。
-   **メインカレンダー詳細ポップアップの新規実装**:
    -   イベント詳細情報を返すAPIエンドポイント (`/calendario/event/<id>/details`) を `app/calendario/routes.py` に作成。
    -   APIを呼び出してイベント詳細を表示する `showEventDetails` 関数を `static/js/calendario.js` に新規作成（汎用ポップアップ `showCalendarioPopup` を利用）。
    -   `app/calendario/templates/calendario/month_view.html` の詳細ボタンを修正し、新しい `showEventDetails` 関数を呼び出すように変更。
-   **シフト管理警告ポップアップの新規実装とUI改善**:
    -   警告表示用の `showWarningDetails` 関数を `static/js/calendario.js` に新規作成（汎用ポップアップ `showCalendarioPopup` を利用）。
    -   `app/calendario/templates/calendario/shift_manager.html` から古い静的な警告表示UI（モーダル）を削除。
    -   `static/js/shift_manager.js` の違反アイコンクリック時の処理を、新しい `showWarningDetails` 関数を呼び出すように修正。
-   **「出張」ジャンルのイベントカラー変更**: `static/css/style.css` で `.event-shucchou` の背景色をゴールドに、文字色を暗い色に変更。
-   **予定ボックス内移動ボタンの配置調整試行**: `static/css/style.css` で `.event-grid-item` に `position:relative` と右パディングを、`.btn-custom-move` に絶対配置スタイルを追加（レイアウトの最終調整は今後の課題）。
-   **カレンダー表示幅の柔軟性向上**: `static/css/style.css` に `.calendar-container` と `.calendar-table` のための新しいスタイルルールを追加し、幅自動調整とレスポンシブ対応の基礎を導入（HTML側でのクラス適用は別途必要）。

## 残存する問題・要確認事項 (2025-06-09時点)

-   **カレンダー幅自動調整CSSのHTML適用**: 新しく追加したCSSクラス `.calendar-container` および `.calendar-table` を、実際のHTMLテンプレート (`month_view.html`, `week_view.html`, `shift_manager.html` 等) の適切な要素に適用し、期待通りに動作するか確認が必要です。
-   **予定ボックスのアクションボタンレイアウト**: `.event-grid-item` 内の移動ボタン (`.btn-custom-move`) を絶対配置するCSS修正を行いましたが、他のアクションボタン（詳細、編集、コピー）との兼ね合いでレイアウトが崩れる可能性があります。アクションボタン群全体の配置方法について、より堅牢な方法（例: `.event-actions` コンテナ自体を絶対配置し、テキスト部分のマージンで調整する等）を検討・実装する必要があります。
-   **`start_time` / `end_time` のバックエンド処理**: `routes.py` で `start_time` を参照するようにしましたが、`utils.py` 内の `add_event` や `update_event` が `start_time` と `end_time` を個別に正しく処理・保存できるか、また、`end_time` がフォームからどのように渡され、処理されるかの確認が必要です。現状、`routes.py` の修正では `updated_event_data` に `time` として `start_time` のみを渡しています。

## 過去に解決した問題

-   (必要に応じて、以前のセッションで解決した問題をここに移動・記載)
