# Famigliapp TODO List

## Introduction

This document outlines pending tasks, unimplemented features based on original specifications, and potential areas for enhancement for the Famigliapp application. The application is currently in a mature prototype stage with many core features implemented for both CLI and Web interfaces. This list aims to guide further development towards a more robust and feature-complete state.

## Unimplemented or Partially Implemented Specifications/Features

This section lists items derived from the `about this app.txt` specification document that appear to be not yet fully implemented or require clarification and potential further development.

*   **Scatola di Capriccio (Feedback & Survey Box):**
    *   Clarify and potentially implement user-to-user feedback if originally intended (current model seems user-to-admin for feedback).
    *   Enhance UI/UX for admin survey creation, target user selection, and management of responses.
    *   Review notification system for surveys to ensure it aligns with "全員に通知" (notify all targeted users) if complex targeting is used.
*   **Quest Box (Task Management):**
    *   Develop a more detailed UI for managing the full lifecycle: progress reporting by assignees, and confirmation of completion by issuers.
    *   Implement specific logic and tracking for "cash reward" handling beyond just a text field (e.g., logging payouts, status).
*   **File Uploads (Corso, Seminario, Monsignore, Intrattenimento, Principessina):**
    *   While uploads are supported, implement robust handling for video files: size limits, format validation, potential for streaming vs. direct download, thumbnail generation.
    *   Ensure consistent file management across modules (storage, deletion).
*   **Daily Reminders (Corso, Seminario, Monsignore, Intrattenimento, Principessina):**
    *   Verify the robustness and accuracy of daily reminder notifications (e.g., "until feedback is posted"). Ensure tasks are correctly tracking status and triggering reminders appropriately for all specified modules.
    *   Consider user-configurable reminder preferences (e.g., opt-out for certain modules).
*   **Calendario (Shared Calendar & Shift Management):**
    *   Review notification granularity: `about this app.txt` implies "編集が行われるたびに編集者と、編集内容が全員に通知される" (every edit, with details, to everyone). Ensure current notifications match this detail or enhance if they are summary-based.
    *   Enhance the UI for displaying shift rule warnings to make them more prominent and actionable for admins during shift planning.
*   **Resoconto (Work Reports & AI Analysis):**
    *   Develop a dedicated admin interface/workflow for reviewing AI analysis and efficiently allocating points based on it. Current point allocation is manual and separate.
*   **Invite System:**
    *   Clarify and potentially implement the workflow for how new users utilize invite codes for registration/first login if this is not fully fleshed out in the web version.

## Enhancements for Existing Features

*   **General File Attachments:**
    *   Implement security scanning/sanitization for all uploaded files.
    *   Develop preview capabilities for common file types directly in the web UI.
*   **Notification System:**
    *   Provide user-level settings to configure notification preferences (e.g., choose delivery channels, opt-out of certain non-critical notifications).
    *   Improve content and formatting of notification messages for clarity.
*   **Punto (Points System):**
    *   Full integration of Quest Box rewards (A-points) into the Punto system.
    *   Consider more detailed logging or categories for point consumption/earning if needed for advanced auditing.
*   **UI/UX (Web Version):**
    *   Unify design language and user experience across all modules.
    *   Improve mobile-friendliness and responsiveness.
    *   Enhance CLI usability with clearer prompts, more consistent output formatting.
*   **Search Functionality:**
    *   Explore options for a global, cross-module search feature.
    *   Improve search accuracy and relevance ranking.
*   **Admin Panel/Dashboard:**
    *   Develop a centralized web-based admin panel for managing users (beyond `config.py`), viewing system logs, managing data across modules (e.g., bulk operations), and application settings.

## Bug Fixes & Stability

*   **Error Handling:** Conduct a comprehensive review of error handling across both CLI and web components, especially for file I/O, API interactions, and data parsing.
*   **JSON File Performance:** For modules with potentially large JSON files (e.g., posts, history), investigate and implement strategies to mitigate performance degradation (e.g., data archiving, pagination for reads, more efficient writes).
*   **Input Validation:** Strengthen input validation across all forms (CLI and Web) to prevent errors and potential security issues.
*   **Concurrency:** Review and test behavior if multiple users/processes attempt to write to the same JSON file simultaneously (though less of an issue with Flask's typical single-worker dev server, important for production).

## Testing

*   **Unit Tests:** Increase unit test coverage for utility functions, business logic in each module, and data handling functions.
*   **Integration Tests:** Develop more integration tests for interactions between different modules (e.g., Quest rewards affecting Punto).
*   **UI Testing (Web):** Introduce UI testing using frameworks like Selenium or Playwright to automate testing of web application workflows.

## Documentation

*   **API Documentation:** If any RESTful APIs are exposed (even internally), document them using standards like OpenAPI.
*   **Developer Documentation:** Expand on code comments, add module-level documentation explaining architecture and data flow for easier onboarding of new developers.
*   **User Manuals:** Create user guides for both CLI and Web versions, explaining features and usage for end-users (especially admins).

## Refactoring & Technical Debt

*   **Data Persistence Strategy:** Review the hybrid JSON/SQLAlchemy approach. Identify if more modules should migrate to SQLAlchemy for better data integrity, querying, and scalability, or if the current JSON approach is adequate for the project's scale and privacy goals.
*   **Code Deduplication:** Identify and refactor common patterns or duplicated code (e.g., similar filtering logic in different modules) into shared utilities.
*   **Modularity:** Further improve modularity between blueprints to reduce tight coupling.
*   **Configuration Management (`config.py`):** Review the structure of `config.py`. Consider using environment variables for sensitive information (API keys, secret key) rather than hardcoding, especially for any potential deployment.
*   **Front-end Assets:** For the web version, consider using tools for managing and bundling CSS/JS assets if complexity grows.
