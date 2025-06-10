// Ensure editEvent is globally available
if (typeof window.editEvent === 'undefined') {
    window.editEvent = function(eventId) {
        // console.log('Attempting to navigate to edit page for event ID (global):', eventId); // Optional logging
        window.location.href = `/calendario/edit/${eventId}`;
    };
}

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

// Function to truncate long event titles
function truncateEventTitle(title, maxLength = 20) {
    if (title.length > maxLength) {
        return title.substring(0, maxLength) + '...';
    }
    return title;
}

$(document).ready(function() {
    // Details Button
    $(document).on('click', '.event-details-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const eventId = $(this).data('event-id');
        const cellElement = $(this).closest('td')[0]; // Get the raw DOM element
        if (typeof showEventDetails === 'function') {
            showEventDetails(eventId, cellElement);
        } else {
            console.error('showEventDetails function is not defined for event ID:', eventId);
        }
    });

    // Edit Button
    $(document).on('click', '.event-edit-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const eventId = $(this).data('event-id');
        if (typeof editEvent === 'function') { // This refers to window.editEvent
            editEvent(eventId);
        } else {
            // This else block should ideally not be reached if window.editEvent is correctly defined.
            console.error('Global editEvent function is not defined. Attempting direct navigation for event ID:', eventId);
            window.location.href = `/calendario/edit/${eventId}`; // Fallback
        }
    });

    // Move Button
    $(document).on('click', '.event-move-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const eventId = $(this).data('event-id');
        console.log('Move button clicked for event ID:', eventId);
        // Placeholder for existing move functionality integration
        // Example: if there's a global function like `initiateMoveProcess(eventId)`
        // if (typeof initiateMoveProcess === 'function') {
        //     initiateMoveProcess(eventId);
        // } else {
        //     console.warn('Move functionality not yet fully implemented for this button.');
        // }
    });

    // Shift Event Copy Button (and potentially other .btn-custom-copy buttons)
    $(document).on('click', '.btn-custom-copy', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const eventId = $(this).data('event-id');
        console.log('Copy button clicked for event ID:', eventId);
        // Placeholder for copy functionality
        // Example: if there's a global function like `copyEvent(eventId)`
        // if (typeof copyEvent === 'function') {
        //     copyEvent(eventId);
        // } else {
        //     console.warn('Copy functionality not yet implemented for this button.');
        // }
    });
});
