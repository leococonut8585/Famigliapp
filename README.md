# Famigliapp: Your Private Family & Community Hub

**Famigliapp** is a versatile, private application designed to foster connection, organization, and fun within families or small communities. It combines practical tools with engaging features to manage daily life and strengthen bonds.

## Overview

Famigliapp serves as a central digital space for family members or a close-knit group. It offers a suite of tools ranging from shared calendars and task management to unique point systems and various themed bulletin boards for different types of interaction. Initially prototyped as a CLI application, it has evolved to include a Flask-based web interface, offering a richer user experience. The application supports notifications via email, LINE Notify, and Pushbullet, and even incorporates AI for analyzing work reports.

## Current Development Status

The application includes a wide array of functional modules, accessible via both a command-line interface (CLI) and a Flask web application. Key features such as point management, diverse bulletin boards (for general posts, audio praise, feedback, media sharing), shared calendar with shift management, task management (Quest Box), and various reporting/utility functions are implemented. The system uses a hybrid data storage approach with JSON files for many features and SQLAlchemy for core user data. Notification systems and AI integration for text analysis are also in place.

## Key Features

Famigliapp is composed of several distinct modules, each catering to different needs:

*   **User Authentication:** Secure login system with predefined user accounts and roles (admin, user). Passwords are not stored in plain text (implied by standard Flask practices, though not explicitly detailed in provided files).
*   **Punto (Points System):**
    *   Manages user points: `AhvPunto` (A points), `OzePunto` (O points), and `UnitoPunto` (A - O, auto-calculated).
    *   Admin can edit points. Users can view their own points.
    *   Point changes trigger email notifications.
    *   Features include point history, rankings (weekly, monthly, yearly, all-time, growth rate), and graph visualization.
    *   Data primarily stored in `points.json` and `points_history.json`.
*   **Posts (Generic Bulletin Board):**
    *   General purpose posting and viewing.
    *   Supports categories, author filtering, keyword search, and date range filtering.
    *   Users can edit their own posts; admins can edit/delete any post.
    *   Supports comments on posts.
    *   Data stored in `posts.json` and `comments.json`.
*   **Bravissimo! (Audio Praise Board):**
    *   Admins can upload audio praise messages directed at specific users.
    *   Targeted users receive notifications.
    *   Allows searching by date, sender, and recipient.
    *   All users can listen and save audio files.
    *   Data and uploaded files managed by the `bravissimo` module.
*   **Intrattenimento (Entertainment Sharing):**
    *   Users share thoughts and media (audio/video) on entertainment.
    *   Supports titles, body text, optional file uploads, and an expiration date for posts.
    *   Features filtering by author, keyword, and date range.
    *   Expired posts are hidden from regular users but accessible to admins.
    *   Includes a daily reminder (8 PM) for users who haven't posted.
    *   Data in `intrattenimento.json`, uploads in `static/uploads`.
*   **Corso (Course/Seminar Feedback):**
    *   Platform for users to post feedback on courses or seminars they've attended.
    *   Supports file uploads (e.g., seminar materials, audio/video).
    *   Features filtering by author and keyword search.
    *   Posts can have an expiration date, after which they are hidden from regular users but retained for admins.
    *   Data in `corso.json`, uploads in `static/uploads`.
*   **Seminario (Lesson Feedback & Scheduling):**
    *   Users post feedback on lessons/tutoring sessions.
    *   Users can register lesson dates; receives daily reminders to post feedback for past, un-commented lessons.
    *   Supports filtering by author and keyword.
    *   Data in `seminario.json`.
*   **Principessina (Baby Reports):**
    *   Primarily for babysitters/staff to report on a child's status.
    *   Supports text, image, and video uploads.
    *   All users can view; features filtering by poster and keyword.
    *   Includes a daily reminder for all users to post.
    *   Data in `principessina.json`, media likely in `static/uploads`.
*   **Monsignore (Image-based Column/Feedback):**
    *   Users and admins can upload images (e.g., columns, articles).
    *   Users can post comments/feedback on these images.
    *   Supports filtering by upload date and keyword search.
    *   Includes a daily reminder to post feedback on un-commented images.
    *   Data in `monsignore.json`, uploads in `static/uploads`.
*   **Scatola di Capriccio (Feedback & Survey Box):**
    *   Users can submit feedback and suggestions.
    *   Content is visible only to administrators.
    *   Admins can post surveys targeted at specific users, triggering notifications.
    *   Data in `scatola_capriccio.json` and `scatola_surveys.json`.
*   **Quest Box (Task Management):**
    *   Users and admins can post tasks or requests.
    *   Admins can define participation conditions, deadlines, and rewards (A-points or monetary).
    *   Tasks can be assigned to specific users or open for acceptance.
    *   Users can accept quests, report progress, and mark as complete (requiring confirmation from the issuer).
    *   Data in `quests.json`.
*   **Vote Box (Voting/Polls):**
    *   Allows users to create and participate in polls.
    *   Features include creating votes, viewing open/closed votes, and seeing vote details.
    *   Data likely in `votebox.json`.
*   **Nedari Box (Requests/Begging):**
    *   A space for users to make requests for items or favors.
    *   Data likely in `nedari.json`.
*   **Calendario (Shared Calendar & Shift Management):**
    *   Shared calendar for events. Users can add, edit (own), and view events.
    *   Event modifications trigger notifications to all users.
    *   **Shift Management (Admin only):**
        *   Visual drag-and-drop interface for assigning employees to shifts.
        *   Warnings for rule violations (max consecutive workdays, min staff per day, forbidden/required pairings, attribute requirements).
        *   Employee attributes (A, B, C, D) can be defined for rule-based warnings.
        *   Displays ongoing work/off day counts for employees.
        *   Calendar statistics (work/off days per employee) viewable.
    *   Data in `events.json` and `calendar_rules.json`.
*   **Resoconto (Work Reports & AI Analysis):**
    *   Users submit daily work reports.
    *   Reports are processed daily (4 AM) by an AI (Claude API) to generate summaries, rankings, and critiques visible to admins.
    *   Admins can view all reports and AI analysis; users can view their own.
    *   Features report counts ranking and CSV export.
    *   Data in `resoconto.json`.
*   **Invite System:**
    *   Admins can generate invite codes for new users to join.
    *   Data in `invites.json`.
*   **Notification System:**
    *   Core events (point changes, new posts in some modules, calendar edits) trigger notifications.
    *   Supports Email, LINE Notify, and Pushbullet.
    *   Configuration in `config.py`.

## Technology Stack

*   **Backend:** Python, Flask
*   **Database:** Primarily JSON files for most features. SQLAlchemy and SQLite are used for core models like User, Post, and PointsHistory (see `app/models.py`). Alembic is used for SQLAlchemy database migrations.
*   **Frontend:** Jinja2 for templating, HTML, CSS, JavaScript.
*   **Forms:** Flask-WTF for web forms.
*   **Scheduling:** APScheduler for reminder tasks and daily report processing.
*   **AI Integration:** Anthropic Claude API for Resoconto analysis (requires API key).
*   **Notifications:** Email (Flask-Mail), LINE Notify, Pushbullet.
*   **Development Server:** Werkzeug (via `flask run`).

## Directory Structure and Key File Roles

*   **`run.py`**: Main entry point for the CLI application and for launching the Flask web server via `flask run`.
*   **`config.py`**: Contains application configuration, including user credentials, file paths for JSON data, API keys, and notification settings.
*   **`requirements.txt`**: Lists Python package dependencies.
*   **`app/`**: Main application package.
    *   **`__init__.py`**: Application factory (`create_app`), initializes Flask extensions, registers blueprints.
    *   **`models.py`**: Defines SQLAlchemy database models (User, Post, PointsHistory).
    *   **`utils.py`**: General utility functions for the application.
    *   **`<module_name>/` (e.g., `app/punto/`, `app/calendario/`)**: Individual feature modules (blueprints). Typically contain:
        *   `__init__.py`: Blueprint registration.
        *   `routes.py`: Defines web routes and view functions for the module.
        *   `forms.py`: Defines WTForms for web input.
        *   `utils.py`: Module-specific utility functions and data handling (often interacting with JSON files).
        *   `tasks.py`: Module-specific scheduled tasks (if any).
        *   `templates/<module_name>/`: Jinja2 templates for the module's web pages.
*   **`static/`**: Static files (CSS, JavaScript, images, user uploads).
*   **`migrations/`**: Alembic database migration scripts for SQLAlchemy models.
*   **Data Files (`*.json`)**: Located in the project's root directory, storing data for various features (e.g., `points.json`, `events.json`). These are typically created automatically on first use.

## Setup and Execution

### Prerequisites

*   Python 3 (e.g., 3.8+)
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  Review `config.py`.
2.  **`USERS`**: Define user accounts, passwords, roles, and emails in the `USERS` dictionary.
3.  **`SECRET_KEY`**: Change this to a strong, unique random string for session management in a production-like environment.
4.  **API Keys & Tokens (Optional):**
    *   `LINE_NOTIFY_TOKEN`: For LINE notifications.
    *   `PUSHBULLET_TOKEN`: For Pushbullet notifications.
    *   `ANTHROPIC_API_KEY` (or ensure the relevant environment variable is set for Claude API access, as used in `resoconto/tasks.py`).
5.  **Mail Settings (Optional):**
    *   Set `MAIL_ENABLED = True` to enable email notifications.
    *   Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_SENDER`, and potentially `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_USE_SSL` depending on your email provider.

### Database Setup

*   **SQLAlchemy Database (User, Post, PointsHistory):**
    The application uses Flask-Migrate for database schema migrations. Ensure `FLASK_APP=run.py` is set in your environment.
    ```bash
    # Initialize migrations directory (only if it doesn't exist)
    # flask db init

    # Generate a new migration script after changes to SQLAlchemy models in app/models.py
    # flask db migrate -m "Brief description of model changes"

    # Apply the latest migrations to the database (creates or updates tables)
    flask db upgrade
    ```
    A SQLite database file (`famigliapp.db`) will be created in the project root by default.
*   **JSON Data Files:** Most other data (points, module-specific posts, calendar events, etc.) are stored in JSON files (e.g., `points.json`, `events.json`) in the project root. These are generally created automatically when features are first used.

### Running the Application

**1. Command-Line Interface (CLI):**
```bash
python run.py
```
You will be prompted for your username and password.

**2. Web Application (for development):**
Ensure your `FLASK_APP` environment variable is set:
```bash
# On macOS/Linux:
export FLASK_APP=run.py
# On Windows (Command Prompt):
# set FLASK_APP=run.py
# On Windows (PowerShell):
# $env:FLASK_APP = "run.py"

flask run
```
The application will typically be available at `http://127.0.0.1:5000/`. For production, use a proper WSGI server like Gunicorn or uWSGI.

## Data Management

Famigliapp uses a hybrid data storage approach:
*   **SQLAlchemy (SQLite by default):** Manages core, structured data like user accounts, generic posts, and point transaction history. This provides relational integrity for these key entities.
*   **JSON Files:** Feature-specific data for most modules (e.g., balances in `points.json`, individual module posts, calendar events, configurations) are stored in separate JSON files in the project root. This approach was likely chosen for simplicity during rapid prototyping and ease of inspection.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
