# Project Status - Famigliapp Calendario

## Last Updated: 2025-06-08

### Recent Changes (Famigliapp Calendario機能修正 第2弾):

*   **TypeError Fix:** Corrected `isinstance()` usage in `app/calendario/utils.py` by ensuring `time` from `datetime` is correctly imported and used.
*   **Time Selection UI:**
    *   Updated `app/calendario/forms.py` to use `SelectField` for event start and end times, providing a scrollable list of 15-minute intervals.
    *   Added CSS to `static/css/style.css` for styling and enabling scroll functionality for these select boxes.
*   **Event Details Popup:**
    *   Replaced the previous event detail display with a dynamic JavaScript popup in `static/js/calendar_event_details.js`.
    *   Added CSS to `static/css/style.css` for the popup's appearance and animation.
*   **Standardized Warning Popups:**
    *   Refactored JavaScript to create a generic popup function `showCalendarioPopup`.
    *   Updated shift management warnings (`static/js/shift_manager.js`) and form validation alerts (`static/js/shift_rules.js`) to use this new popup system, enhancing UI consistency.
*   **Event Genre Colors:** Updated CSS in `static/css/style.css` for `.event-tattoo`, `.event-mammy`, `.event-lesson`, and `.event-trip` with new background colors.
*   **Event Box Optimization:** Adjusted CSS in `static/css/style.css` for `.event-grid-item`, `.event-actions`, and calendar cells to reduce padding/margins, optimize button sizes, and manage cell content overflow.

## 2025-06-09 セッション (Jules)

以下の修正を実施しました。

1.  **編集フォームのテンプレートエラー修正**: `event_form.html` で `form.time` を `form.start_time` と `form.end_time` に対応。関連するJavaScriptも修正。
2.  **日付セルの幅調整**: `style.css` でカレンダーセル幅を `180px` に拡大し、関連する要素の幅も調整。
3.  **詳細ボタンのイベントハンドリング修正**: `month_view.html` と `calendar_event_details.js` を修正。古いUI（Bootstrapモーダル）を削除し、`showCalendarioPopup` を使用する新しいカスタムポップアップでイベント詳細を表示するように変更。
4.  **シフト管理エリアのカレンダー表示範囲修正**: `routes.py` の `/shift` ルートを修正し、表示月全体が正しく表示されるようにカレンダーの開始日と終了日の計算ロジックを変更。
5.  **イベントカテゴリのカラー適用修正**: `style.css` に `event-shucchou` を追加、`event-mammy` を `event-mummy` に修正。`routes.py` にカテゴリ名を正規化してCSSクラス名を生成するロジックを追加し、`month_view.html` でそれを適用するように修正。
6.  **シフト管理エリアの警告ポップアップ対応**: `shift_manager.js` 内で `alert()` が使用されていた箇所（違反詳細のJSONパース失敗時）を `showCalendarioPopup` を使用するように統一。
7.  **論理テスト**: 上記修正項目について、期待される動作が実装されていることを論理的に確認。

### 2025-06-09 緊急修正 (Jules)

- Flask起動時の `ModuleNotFoundError: No module named 'app.seminario'` エラーを修正。
    - `wsgi.py`、`tests/test_seminario.py`、`tests/test_seminario_tasks.py` のインポートパスを `app.seminario` から `app.Seminario` に修正。
    - 起動確認テストを実施し、エラーが解消されたことを確認。

## 2025-06-09 Calendarioモジュール修正 (Jules)

Calendarioモジュールの表示問題とエラー修正、UI改善を行いました。

1.  **EventForm 'time' 属性エラー修正**: `routes.py` で `form.start_time` を使用するように変更。
2.  **メインカレンダー詳細ポップアップ実装**: イベント詳細表示用のAPI (`/event/<id>/details`) とJavaScript関数 (`showEventDetails` in `calendario.js`) を新規実装し、汎用ポップアップ (`showCalendarioPopup`) で表示するように `month_view.html` を修正。
3.  **シフト管理警告ポップアップ実装**: 警告表示用のJavaScript関数 (`showWarningDetails` in `calendario.js`) を新規実装し、汎用ポップアップ (`showCalendarioPopup`) で表示するように `shift_manager.js` を修正。`shift_manager.html` から古い警告表示用モーダルを削除。
4.  **カレンダー幅の自動調整**: `style.css` にコンテナ (`.calendar-container`) とテーブル (`.calendar-table`) の幅調整、レスポンシブ対応スタイルを追加（HTML側でのクラス適用は別途必要）。
5.  **出張ジャンルのカラー変更**: `style.css` の `.event-shucchou` の背景色をゴールドに、文字色を暗い色に変更。
6.  **予定ボックスの移動ボタン重なり修正**: `style.css` で `.event-grid-item` に `position:relative` と右パディングを、`.btn-custom-move` に絶対配置スタイルを追加（他のボタンとのレイアウト調整は今後の課題）。
