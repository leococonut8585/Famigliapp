document.addEventListener('DOMContentLoaded', function() {
    // Check if we are on the shift_rules page by looking for a specific element
    const specializedRulesListDisplay = document.getElementById('specialized_rules_list_display');
    if (!specializedRulesListDisplay) {
        // Not on the correct page, or the element is missing. Do nothing.
        return;
    }

    // Initialize specializedRequirements from data passed by the template
    // The template should render: <script> let initialSpecializedRequirements = {{ specialized_requirements|tojson|safe }}; </script>
    // This script should be placed *before* this external JS file, or the data passed some other way.
    // For now, assuming `initialSpecializedRequirements` is globally available or will be made so.
    // Let's try to get it from a global variable if it's set by an inline script in the HTML.
    let specializedRequirements = typeof initialSpecializedRequirements !== 'undefined' ? initialSpecializedRequirements : {};

    const categorySelect = document.getElementById('special_event_category');
    const staffSelect = document.getElementById('special_required_staff');
    const addButton = document.getElementById('add_special_requirement_button');
    const hiddenInput = document.getElementById('specialized_requirements_json_str');

    function renderSpecializedRules() {
        specializedRulesListDisplay.innerHTML = ''; // Clear current display

        if (Object.keys(specializedRequirements).length === 0) {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item text-muted';
            listItem.textContent = '現在、専門予定ルールはありません。';
            specializedRulesListDisplay.appendChild(listItem);
        } else {
            for (const category in specializedRequirements) {
                const staffList = specializedRequirements[category].join(', ');
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                listItem.innerHTML = `<span><strong>${category}:</strong> ${staffList}</span>
                                      <button type="button" class="btn btn-danger btn-sm delete-special-rule" data-category="${category}">削除</button>`;
                specializedRulesListDisplay.appendChild(listItem);
            }
        }
        // Update the hidden input field
        if (hiddenInput) {
            hiddenInput.value = JSON.stringify(specializedRequirements);
        }
    }

    if (addButton) {
        addButton.addEventListener('click', function() {
            const selectedCategory = categorySelect.value;
            const selectedStaff = Array.from(staffSelect.selectedOptions).map(option => option.value);

            if (!selectedCategory) {
                alert('予定ジャンルを選択してください。');
                return;
            }
            if (selectedStaff.length === 0) {
                alert('必須担当者を少なくとも1人選択してください。');
                return;
            }

            specializedRequirements[selectedCategory] = selectedStaff;
            renderSpecializedRules();
        });
    }

    // Event delegation for delete buttons
    specializedRulesListDisplay.addEventListener('click', function(event) {
        if (event.target.classList.contains('delete-special-rule')) {
            const categoryToDelete = event.target.dataset.category;
            if (categoryToDelete && specializedRequirements.hasOwnProperty(categoryToDelete)) {
                delete specializedRequirements[categoryToDelete];
                renderSpecializedRules();
            }
        }
    });

    // Initial render on page load
    renderSpecializedRules();

    // It's good practice to also ensure the hidden field for other rules are populated if this script were to manage them.
    // For now, this script ONLY manages specialized_requirements.
    // The existing hidden fields (forbidden_pairs_hidden etc.) are assumed to be handled by other means or are static.
});
