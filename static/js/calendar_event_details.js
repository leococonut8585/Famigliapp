document.addEventListener('DOMContentLoaded', function () {
    // Use a more specific container if possible, otherwise document
    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('details-btn')) {
            event.preventDefault();
            event.stopPropagation(); // Stop bubbling

            const button = event.target;
            const title = button.dataset.title || '予定の詳細';
            const time = button.dataset.time || '時間指定なし';
            const category = button.dataset.category || 'その他';
            const description = button.dataset.description || '';
            const employee = button.dataset.employee || '';

            let contentHtml = `
                <p><strong>時間:</strong> ${time}</p>
                <p><strong>種類:</strong> ${category}</p>
                <p><strong>説明:</strong> ${description || 'なし'}</p>
            `;

            if (employee) {
                contentHtml += `<p><strong>担当者:</strong> ${employee}</p>`;
            }

            // Assuming showCalendarioPopup is globally available
            // or imported if this is a module
            if (typeof showCalendarioPopup === 'function') {
                showCalendarioPopup(title, contentHtml, button);
            } else {
                console.error('showCalendarioPopup function is not defined.');
                // Fallback or error handling
                alert(`Title: ${title}\nTime: ${time}\nCategory: ${category}\nDescription: ${description}${employee ? '\nEmployee: ' + employee : ''}`);
            }
        }
    });
});
