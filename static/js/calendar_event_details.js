document.addEventListener('DOMContentLoaded', function () {
    const mainContent = document.body; // Or a more specific container if available

    mainContent.addEventListener('click', function (event) {
        const button = event.target.closest('.details-btn');

        if (button) {
            event.preventDefault(); // Good practice, though type="button" shouldn't submit

            const title = button.dataset.title;
            const time = button.dataset.time;
            const description = button.dataset.description;
            const participants = button.dataset.participants; // Comma-separated string or empty
            const category = button.dataset.category;

            const modalElement = document.getElementById('eventDetailModal');
            const modalTitleEl = document.getElementById('eventDetailModalTitle');
            const modalBodyEl = document.getElementById('eventDetailModalBody');

            if (!modalElement || !modalTitleEl || !modalBodyEl) {
                console.error('Modal elements not found. Cannot display event details.');
                alert('詳細表示に必要な要素が見つかりません。');
                return;
            }

            modalTitleEl.textContent = title || '予定の詳細';

            let bodyHtml = '';
            if (time) {
                bodyHtml += `<p><strong>時間:</strong> ${time}</p>`;
            }

            const categoryDisplay = {
                'lesson': 'レッスン',
                'hug': 'ハグの日',
                'kouza': '講座',
                'shucchou': '出張',
                'other': 'その他',
                'shift': 'シフト'
            };
            bodyHtml += `<p><strong>種類:</strong> ${categoryDisplay[category] || category}</p>`;

            if (description) {
                // Escape HTML in description to prevent XSS if description can contain user-input HTML
                const SCRIPT_REGEX = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
                const cleanedDescription = description.replace(SCRIPT_REGEX, '');
                bodyHtml += `<p><strong>メモ/内容:</strong></p><pre style="white-space: pre-wrap; word-break: break-word;">${cleanedDescription}</pre>`;
            } else {
                bodyHtml += `<p><em>メモ/内容はありません。</em></p>`;
            }

            if (participants) {
                bodyHtml += `<p class="mt-2"><strong>対象者:</strong> ${participants.split(',').join(', ')}</p>`; // Ensure spacing if using split
            } else {
                bodyHtml += `<p class="mt-2"><em>対象者はいません。</em></p>`;
            }
            modalBodyEl.innerHTML = bodyHtml;

            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
                modalInstance.show();
            } else {
                console.error('Event Detail Modal element not found or Bootstrap JS not loaded!');
                // Fallback alert
                const fallbackMessage = `タイトル: ${title || 'N/A'}\n` +
                                    `時間: ${time || 'N/A'}\n` +
                                    `種類: ${categoryDisplay[category] || category || 'N/A'}\n` +
                                    `内容: ${description || 'N/A'}\n` +
                                    `対象者: ${participants || 'N/A'}`;
                alert(fallbackMessage);
            }
        }
    });
});
