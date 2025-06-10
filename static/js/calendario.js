// static/js/calendario.js (前回作成したものを修正)
function showEventDetails(eventId, cellElement) {
    // 既存のポップアップを削除 (showCalendarioPopupが行うので、ここでは不要かもしれないが念のため)
    $('.event-popup').remove();
    $('.warning-popup').remove(); // 他のポップアップも消すなら (showCalendarioPopupはevent-popupのみを対象とする)
                                  // showCalendarioPopup 自体が $('.event-popup').remove(); を実行するので、
                                  // ここでの .event-popup の削除は重複するが、害は少ない。
                                  // warning-popup など他のクラスも消したい場合は個別に追加する。

    // APIからデータを取得
    $.get(`/calendario/event/${eventId}/details`, function(data) {
        if (data.error) {
            console.error("Error fetching event details:", data.error);
            const errorTitle = "エラー";
            const errorHtml = `<p>詳細の取得に失敗しました: ${data.error}</p>`;
            // showCalendarioPopup は targetElement を期待する
            // cellElement がDOM要素であることを確認
            showCalendarioPopup(errorTitle, errorHtml, cellElement instanceof jQuery ? cellElement[0] : cellElement, 'error-popup');
            return;
        }

        const title = data.title || '予定の詳細';
        // contentHtml には閉じるボタンは不要 (showCalendarioPopupが自動で追加するため)
        const contentHtml = `
            <p><strong>日時:</strong> ${data.date} ${data.time || ''}</p>
            <p><strong>種類:</strong> ${data.genre}</p>
            <p><strong>説明:</strong> ${data.description || 'なし'}</p>
            <p><strong>担当:</strong> ${data.employee || ''}</p>
        `;

        // 既存の showCalendarioPopup を呼び出す
        // targetElement として cellElement を渡す
        // additionalClass は適宜設定 (例: 'event-details-popup')
        // cellElement がjQueryオブジェクトの場合、DOM要素を渡す
        showCalendarioPopup(title, contentHtml, cellElement instanceof jQuery ? cellElement[0] : cellElement, 'event-details-popup');

    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Failed to fetch event details:", textStatus, errorThrown);
        const errorTitle = "エラー";
        const errorHtml = `<p>イベント詳細の取得に失敗しました。サーバーエラーが発生した可能性があります。</p>`;
        // showCalendarioPopup は targetElement を期待する
        // cellElement がDOM要素であることを確認
        showCalendarioPopup(errorTitle, errorHtml, cellElement instanceof jQuery ? cellElement[0] : cellElement, 'error-popup');
    });
}

// Ensure jQuery is available, otherwise this code will not work.
// This script assumes jQuery is loaded globally.
// Ensure showCalendarioPopup function is available (e.g., loaded from calendar_event_details.js or a shared utility script)
// and that it is loaded BEFORE this script if in separate files.


// static/js/calendario.js (既存の showEventDetails の下などに追加)

function showWarningDetails(warningType, details, cellElement) {
    // 既存のポップアップを削除 (showCalendarioPopupが行うので、ここでは不要かもしれないが念のため)
    // showCalendarioPopup は .event-popup を削除するので、warning-popup も削除対象に含める
    $('.event-popup').remove();
    $('.warning-popup').remove(); // 自分自身も消す

    const title = '<h5 style="color: #856404;">⚠️ ルール違反</h5>'; // タイトルは固定または warningType に応じて変更
    const contentHtml = `<p>${details}</p>`;

    // 既存の showCalendarioPopup を呼び出す
    // targetElement として cellElement を渡す
    // additionalClass として 'warning-popup' や、warningType に応じたクラスを指定可能
    let popupClass = 'warning-popup';
    // if (warningType === 'someSpecificType') {
    //     popupClass += ' specific-warning-class';
    // }

    // showCalendarioPopup は targetElement として DOM Element を期待する
    const targetDomElement = (cellElement instanceof jQuery) ? cellElement[0] : cellElement;

    showCalendarioPopup(title, contentHtml, targetDomElement, popupClass);
}
