// Ensure editEvent is globally available
if (typeof window.editEvent === 'undefined') {
    window.editEvent = function(eventId) {
        // console.log('Attempting to navigate to edit page for event ID (global):', eventId); // Optional logging
        window.location.href = `/calendario/edit/${eventId}`;
    };
}

// Existing global functions from calendario.js
function showEventDetails(eventId, cellElement) {
    $('.event-popup').remove();
    $('.warning-popup').remove();

    $.get(`/calendario/event/${eventId}/details`, function(data) {
        if (data.error) {
            console.error("Error fetching event details:", data.error);
            const errorTitle = "エラー";
            const errorHtml = `<p>詳細の取得に失敗しました: ${data.error}</p>`;
            showCalendarioPopup(errorTitle, errorHtml, cellElement instanceof jQuery ? cellElement[0] : cellElement, 'error-popup');
            return;
        }
        const title = data.title || '予定の詳細';
        const contentHtml = `
            <p><strong>日時:</strong> ${data.date} ${data.time || ''}</p>
            <p><strong>種類:</strong> ${data.genre}</p>
            <p><strong>説明:</strong> ${data.description || 'なし'}</p>
            <p><strong>担当:</strong> ${data.employee || ''}</p>
        `;
        showCalendarioPopup(title, contentHtml, cellElement instanceof jQuery ? cellElement[0] : cellElement, 'event-details-popup');
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Failed to fetch event details:", textStatus, errorThrown);
        const errorTitle = "エラー";
        const errorHtml = `<p>イベント詳細の取得に失敗しました。サーバーエラーが発生した可能性があります。</p>`;
        showCalendarioPopup(errorTitle, errorHtml, cellElement instanceof jQuery ? cellElement[0] : cellElement, 'error-popup');
    });
}

function showWarningDetails(warningType, details, cellElement) {
    $('.event-popup').remove();
    $('.warning-popup').remove();
    const title = '<h5 style="color: #856404;">⚠️ ルール違反</h5>';
    const contentHtml = `<p>${details}</p>`;
    const targetDomElement = (cellElement instanceof jQuery) ? cellElement[0] : cellElement;
    showCalendarioPopup(title, contentHtml, targetDomElement, 'warning-popup');
}

function truncateEventTitle(title, maxLength = 20) {
    if (title.length > maxLength) {
        return title.substring(0, maxLength) + '...';
    }
    return title;
}

// New event handlers wrapped in DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Details Button for non-shift events
    $(document).on('click', '.btn-event-details', function(e) {
        e.preventDefault();
        const eventId = $(this).data('event-id');
        const cellElement = $(this).closest('td')[0];
        if (typeof showEventDetails === 'function') {
            showEventDetails(eventId, cellElement);
        } else {
            console.error('showEventDetails function is not defined.');
        }
    });

    // Edit Button for non-shift events
    $(document).on('click', '.btn-event-edit', function(e) {
        e.preventDefault();
        const eventId = $(this).data('event-id');
        if (typeof editEvent === 'function') {
            editEvent(eventId);
        } else {
            console.error('Global editEvent function is not defined. Attempting direct navigation.');
            window.location.href = `/calendario/edit/${eventId}`;
        }
    });

    // Copy Button for non-shift events
    $(document).on('click', '.btn-event-copy', function(e) {
        e.preventDefault();
        const eventId = $(this).data('event-id');
        const cellElement = $(this).closest('td');
        const currentDate = cellElement.data('date');

        if (!currentDate) {
            alert('日付が取得できませんでした。');
            return;
        }

        if (confirm('この予定をコピーしますか？')) {
            $.ajax({
                url: (typeof apiEventDropUrl !== 'undefined' ? apiEventDropUrl : '/calendario/api/event/drop'),
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    event_id: eventId,
                    new_date: currentDate,
                    operation: 'copy'
                }),
                success: function(response) {
                    alert('予定をコピーしました');
                    location.reload();
                },
                error: function(xhr, status, error) {
                    let errorMsg = 'コピーに失敗しました';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMsg += ': ' + xhr.responseJSON.message;
                    } else if (error) {
                        errorMsg += ': ' + error;
                    }
                    alert(errorMsg);
                }
            });
        }
    });

    // Move Button for non-shift events
    $(document).on('click', '.btn-event-move', function(e) {
        e.preventDefault();
        const $eventItem = $(this).closest('.event-item');
        const eventId = $(this).data('event-id');

        $eventItem.addClass('moving-mode');
        alert('移動先の日付をクリックしてください');

        $('.calendar-day').off('click.moveEvent');

        $('.calendar-day').one('click.moveEvent', function() {
            const newDate = $(this).data('date');
            if (newDate) {
                $.ajax({
                    url: (typeof apiEventDropUrl !== 'undefined' ? apiEventDropUrl : '/calendario/api/event/drop'),
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        event_id: eventId,
                        new_date: newDate,
                        operation: 'move'
                    }),
                    success: function(response) {
                        location.reload();
                    },
                    error: function(xhr, status, error) {
                        let errorMsg = '移動に失敗しました';
                        if (xhr.responseJSON && xhr.responseJSON.message) {
                            errorMsg += ': ' + xhr.responseJSON.message;
                        } else if (error) {
                            errorMsg += ': ' + error;
                        }
                        alert(errorMsg);
                        $eventItem.removeClass('moving-mode');
                    }
                });
            } else {
                alert('有効な日付セルを選択してください。');
                $eventItem.removeClass('moving-mode');
            }
        });
    });

    // Placeholder Handlers for Shift Event Buttons (as per previous structure in month_view)
    // These target .btn-custom-copy and .btn-custom-move which are used by shift items
    $(document).on('click', '.shift-grid-item .btn-custom-copy', function(e) {
        e.preventDefault();
        const eventId = $(this).data('event-id');
        console.log('Shift Copy button clicked for event ID:', eventId);
        alert('シフトのコピー機能は別途実装されます。Event ID: ' + eventId);
    });

    $(document).on('click', '.shift-grid-item .btn-custom-move', function(e) {
        e.preventDefault();
        const eventId = $(this).data('event-id');
        console.log('Shift Move button clicked for event ID:', eventId);
        alert('シフトの移動機能は別途実装されます。Event ID: ' + eventId);
    });
});
