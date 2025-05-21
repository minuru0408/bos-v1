import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

_scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_sheet():
    """Return the Google Sheet handle or ``None`` if unavailable."""
    creds_path = os.getenv("GOOGLE_SHEETS_CREDS")
    if not creds_path or not os.path.exists(creds_path):
        return None
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, _scope)
        client = gspread.authorize(creds)
        return client.open("HECTOR_Memory_Log").sheet1
    except Exception as e:
        print(f"[memory] Google Sheets logging disabled: {e}")
        return None

def log_message(role, text):
    """Append a timestamped message (role + text) to Google Sheet."""
    sheet = _get_sheet()
    if not sheet:
        # Fallback: just print locally so conversations still work
        print(f"[memory] {role}: {text}")
        return
    try:
        sheet.append_row([role, text, datetime.now().isoformat()])
    except Exception as e:
        # Swallow errors so the caller isn't impacted
        print(f"[memory] Failed to log message: {e}")

def load_memory(limit=20):
    """Fetch the last `limit` messages from the sheet as a list of {role,content}."""
    sheet = _get_sheet()
    if not sheet:
        return []
    try:
        # Get all rows, keep only the last `limit`
        all_rows = sheet.get_all_values()  # each row = [role, text, timestamp]
        recent = all_rows[-limit:]
    except Exception as e:
        print(f"[memory] Failed to load memory: {e}")
        return []

    messages = []
    for row in recent:
        role, text, *_ = row
        messages.append({"role": role, "content": text})
    return messages

