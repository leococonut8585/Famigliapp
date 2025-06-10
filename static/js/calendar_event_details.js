// Globally accessible function for creating popups
function showCalendarioPopup(title, contentHtml, targetElement, additionalClass = '') {
    $('.event-popup').remove(); // Remove any existing popups

    let popupClasses = 'event-popup';
    if (additionalClass) {
        popupClasses += ' ' + additionalClass;
    }

    const popupHTML = `
        <div class="${popupClasses}">
            <div class="popup-content">
                ${title ? `<h3>${title}</h3>` : ''}
                <div>${contentHtml}</div>
                <button class="close-popup">閉じる</button>
            </div>
        </div>
    `;

    const $popup = $(popupHTML);

    if (targetElement) {
        const targetRect = targetElement.getBoundingClientRect();
        const scrollTop = $(window).scrollTop();
        const scrollLeft = $(window).scrollLeft();

        $popup.css({
            position: 'absolute',
            top: targetRect.bottom + scrollTop + 5, // 5px below the button/element
            left: targetRect.left + scrollLeft,
            'z-index': 1000
        });
    } else {
        // Fallback positioning: center of the viewport
        $popup.css({
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            'z-index': 1000
        });
    }

    $('body').append($popup);

    $popup.find('.close-popup').on('click', function() {
        $popup.remove();
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const calendarContainer = document.querySelector('.calendar-scroll-container'); // More specific container

    if (calendarContainer) {
        calendarContainer.addEventListener('click', function (event) {
            const button = event.target.closest('.details-btn');

            if (button) {
                event.preventDefault();
                event.stopPropagation();

                const title = button.dataset.title || '予定の詳細';
                const time = button.dataset.time || '';
            const category = button.dataset.category || '';
            const description = button.dataset.description || '';
            // Participants and employee are not used in the generic popup structure directly,
            // but were part of the original eventData. For warnings, this is fine.
            // For event details, we construct the HTML content for the popup.

            let contentHtml = `<p><strong>時間:</strong> ${time || '指定なし'}</p>
                               <p><strong>種類:</strong> ${category || '指定なし'}</p>`;

            const employee = button.dataset.employee || '';
            if (employee) {
                contentHtml += `<p><strong>担当:</strong> ${employee}</p>`;
            }
            const participants = button.dataset.participants || '';
            if (participants) {
                contentHtml += `<p><strong>対象者:</strong> ${participants}</p>`;
            }

            contentHtml += `<p><strong>内容:</strong></p>
                            <pre style="white-space: pre-wrap; word-break: break-word;">${description || 'なし'}</pre>`;

            showCalendarioPopup(title, contentHtml, button);
        }
    });
    } // end if (calendarContainer)
});
