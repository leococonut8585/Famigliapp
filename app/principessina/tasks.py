from datetime import date, datetime, timedelta 
from typing import List, Dict, Any 

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover - optional dependency
    BackgroundScheduler = None

scheduler = BackgroundScheduler() if BackgroundScheduler else None

import config
from app.utils import send_email 
from . import utils 
from app.calendario import utils as calendario_utils # Import Calendario utils

admin_overdue_alert_sent_today: Dict[date, bool] = {} 

def get_admin_user_emails() -> List[str]:
    admins = []
    if hasattr(config, "USERS") and isinstance(config.USERS, dict):
        for _, user_data in config.USERS.items():
            if isinstance(user_data, dict) and \
               user_data.get("role") == "admin" and \
               user_data.get("email"):
                admins.append(user_data["email"])
    return admins

def send_decima_report_reminders() -> List[Dict[str, Any]]:
    now = datetime.now()
    current_hour = now.hour
    notified_actions: List[Dict[str, Any]] = [] # Changed variable name for clarity

    is_reporting_window = (11 <= current_hour <= 23) or (0 <= current_hour <= 4)
    if not is_reporting_window:
        return notified_actions

    if current_hour >= 11: reporting_day_date = date.today()
    else: reporting_day_date = date.today() - timedelta(days=1)

    try:
        shift_users_today_usernames = calendario_utils.get_users_on_shift(reporting_day_date)
    except Exception as e: # Catch potential errors like file not found for calendario events
        print(f"Error fetching shift users for {reporting_day_date}: {e}")
        return notified_actions # Exit if we can't determine shift users

    if not shift_users_today_usernames:
        return notified_actions # No users on shift, no reminders to send

    all_reports = utils.load_posts()
    
    for username_on_shift in shift_users_today_usernames:
        user_config = getattr(config, "USERS", {}).get(username_on_shift)
        if not user_config or not user_config.get("email"):
            continue # Skip if user details or email not in config

        user_email = user_config["email"]
        user_has_yura, user_has_mangiato = False, False
        for report in all_reports:
            if report.get("author") == username_on_shift:
                try:
                    if datetime.fromisoformat(report.get("timestamp", "")).date() == reporting_day_date:
                        if report.get("report_type") == "yura": user_has_yura = True
                        elif report.get("report_type") == "mangiato": user_has_mangiato = True
                except ValueError: continue
            if user_has_yura and user_has_mangiato: break

        if not (user_has_yura and user_has_mangiato):
            missing_reports_parts = []
            if not user_has_yura: missing_reports_parts.append("「今日のユラちゃん」")
            if not user_has_mangiato: missing_reports_parts.append("「食べたもの」")
            missing_reports_str = "と".join(missing_reports_parts)
            
            email_subject = "Decima報告リマインダー"
            email_body = (f"今日のDecima報告のうち、{missing_reports_str}の報告がまだのようです。\n"
                          f"投稿期限は本日（または本日開始のシフトの場合、翌朝）4時です。\nご提出をお願いいたします。")
            send_email(email_subject, email_body, user_email)
            notified_actions.append({
                "username": username_on_shift, "status": "reminder_sent", 
                "missing": missing_reports_str, "reporting_day": reporting_day_date.isoformat()
            })
    return notified_actions


def send_decima_overdue_notifications() -> List[Dict[str, Any]]:
    due_reporting_day_date = date.today() - timedelta(days=1)
    notified_actions: List[Dict[str, Any]] = []
    overdue_shift_users_exist = False

    try:
        shift_users_due_usernames = calendario_utils.get_users_on_shift(due_reporting_day_date)
    except Exception as e:
        print(f"Error fetching shift users for {due_reporting_day_date} (overdue check): {e}")
        return notified_actions

    if not shift_users_due_usernames:
        return notified_actions

    all_reports = utils.load_posts()

    for username_on_shift in shift_users_due_usernames:
        user_config = getattr(config, "USERS", {}).get(username_on_shift)
        if not user_config or not user_config.get("email"):
            continue

        user_email = user_config["email"]
        user_has_yura, user_has_mangiato = False, False
        for report in all_reports:
            if report.get("author") == username_on_shift:
                try:
                    if datetime.fromisoformat(report.get("timestamp", "")).date() == due_reporting_day_date:
                        if report.get("report_type") == "yura": user_has_yura = True
                        elif report.get("report_type") == "mangiato": user_has_mangiato = True
                except ValueError: continue
            if user_has_yura and user_has_mangiato: break
        
        if not (user_has_yura and user_has_mangiato):
            overdue_shift_users_exist = True
            missing_reports_parts = []
            if not user_has_yura: missing_reports_parts.append("「今日のユラちゃん」")
            if not user_has_mangiato: missing_reports_parts.append("「食べたもの」")
            missing_reports_str = "と".join(missing_reports_parts)

            email_subject = "【至急】Decima報告が期限切れです"
            email_body = (f"{due_reporting_day_date.strftime('%Y年%m月%d日')}分のDecima報告のうち、{missing_reports_str}が未提出です。\n至急ご提出ください。")
            send_email(email_subject, email_body, user_email)
            notified_actions.append({
                "username": username_on_shift, "status": "overdue_user_notified",
                "missing": missing_reports_str, "due_reporting_day": due_reporting_day_date.isoformat()
            })

    if overdue_shift_users_exist:
        if not admin_overdue_alert_sent_today.get(date.today(), False):
            admin_emails = get_admin_user_emails()
            if admin_emails:
                email_subject = "Decima報告遅延者発生"
                email_body = (f"{due_reporting_day_date.strftime('%Y年%m月%d日')}分のDecima報告について、提出が遅れているシフト担当者がいます。\n"
                              f"詳細はシステムログまたは該当ユーザーへの通知をご確認ください。")
                for admin_email in admin_emails:
                    send_email(email_subject, email_body, admin_email)
                admin_overdue_alert_sent_today[date.today()] = True 
                notified_actions.append({"status": "overdue_admins_notified", "due_reporting_day": due_reporting_day_date.isoformat()})
    return notified_actions

def reset_daily_admin_alert_flag():
    admin_overdue_alert_sent_today.clear()

def archive_old_reports() -> List[int]:
    now = datetime.now()
    active_reports = utils.get_active_reports()
    archived_ids: List[int] = []
    for report in active_reports:
        report_id = report.get("id")
        creation_timestamp_str = report.get("timestamp")
        if not report_id or not creation_timestamp_str: continue
        try: creation_dt = datetime.fromisoformat(creation_timestamp_str)
        except ValueError: continue
        if report.get('status') == 'active' and now >= (creation_dt + timedelta(days=3)):
            if utils.archive_report(report_id):
                archived_ids.append(report_id)
    return archived_ids

def start_scheduler() -> None:
    if scheduler is None: return # pragma: no cover
    if not scheduler.get_jobs(): 
        scheduler.add_job(send_decima_report_reminders, "cron", hour='11-23,0-4', minute=5, id="decima_hourly_reminder")
        scheduler.add_job(send_decima_overdue_notifications, "cron", hour='5-23/2', minute=15, id="decima_overdue_notification")
        scheduler.add_job(reset_daily_admin_alert_flag, "cron", hour=0, minute=1, id="reset_admin_alert_flag")
        scheduler.add_job(archive_old_reports, "cron", hour=1, minute=15, id="archive_decima_reports")
        try: scheduler.start() # pragma: no cover
        except (KeyboardInterrupt, SystemExit): pass # pragma: no cover
        except Exception as e: print(f"Error starting Principessina/Decima scheduler: {e}") # pragma: no cover
    elif not scheduler.running: # pragma: no cover
        try: scheduler.start(paused=False)
        except Exception as e: print(f"Error restarting Principessina/Decima scheduler: {e}") # pragma: no cover
