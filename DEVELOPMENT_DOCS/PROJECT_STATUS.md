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
