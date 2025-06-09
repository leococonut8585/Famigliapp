# Calendario Feature Specifications

## Last Updated: 2025-06-08

### Event Display and Interaction:

*   **Event Details:**
    *   Displayed via a JavaScript popup when an event or "details" button is clicked.
    *   Popup includes: Title, Time (or "All Day"), Genre, Description, Target Employee (if applicable).
    *   Popup is positioned near the triggering element and can be closed via a "Close" button.
*   **Event Creation/Editing Form:**
    *   Start and End times are selected using scrollable dropdowns (`<select>`).
    *   Time options are presented in 15-minute intervals.
*   **Event Genre Colors:**
    *   `.event-tattoo`: Grey (#6c757d)
    *   `.event-mammy`: Dark Red (#8b0000)
    *   `.event-lesson`: Medium Purple (#9370db)
    *   `.event-trip`: Dark Orange (#ff8c00)
*   **Event Box Layout:**
    *   Event items in the calendar view have reduced padding and margins for a compact look.
    *   Action buttons within event items are smaller and arranged horizontally with minimal gaps.
*   **Calendar Cell Overflow:** Date cells in the calendar hide overflowing content by default and show a scrollbar on hover.

### Warnings and Notifications:

*   **Shift Management Warnings:** Displayed using the standard application popup UI.
*   **Form Validation Errors:** Displayed using the standard application popup UI.
*   **General Alerts:** JavaScript `alert()` calls have been replaced with the standard application popup UI.

### Backend (`app/calendario/utils.py`):

*   `update_event` function correctly handles `datetime.time` objects for event time updates.
